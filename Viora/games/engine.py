import asyncio
import random
from datetime import timedelta
from pyrogram import filters
from Viora.config import *
from Viora.core.common import amount, money, now


def reg(app, c):
    e, g, gm, db = c['economy'], c['gems'], c['games'], c['db']
    tasks = {}

    async def stake(uid, n, currency, ref):
        n = int(n)
        if n <= 0:
            return False, 'Stake must be greater than zero.'
        if currency == 'gems':
            return await g.spend(uid, n, 'game_bet', ref)
        return (True, '') if await e.remove(uid, n) else (False, 'Not enough coins.')

    async def refund(gid):
        async with gm.lock(gid):
            game = await gm.get(gid)
            if not game or game.get('status') not in {'joining', 'active'}:
                return False
            r = await db.games.update_one({'game_id': gid, 'status': {'$in': ['joining', 'active']}},
                                          {'$set': {'status': 'refunded', 'finished_at': now()}})
            if not r.modified_count:
                return False
            for x in await gm.entries(gid):
                if x['currency'] == 'gems':
                    await g.add(x['user_id'], x['stake'], 'refund', gid)
                else:
                    await e.add(x['user_id'], x['stake'])
            return True

    async def create(m, typ, n, currency='coins', data=None):
        group = await db.groups.find_one({'chat_id': m.chat.id})
        if group and group.get('gaming_open') is False:
            return None, 'Gaming commands are closed in this group. Use /open.'
        if n <= 0:
            return None, 'Stake must be greater than zero.'
        await e.ensure(m.from_user.id, m.from_user.first_name, m.from_user.username)
        ok, msg = await stake(m.from_user.id, n, currency, f'host:{typ}')
        if not ok:
            return None, msg or 'Insufficient funds.'
        try:
            gid = await gm.create(m.chat.id, typ, m.from_user.id, n, currency, data)
            return gid, ''
        except Exception as ex:
            if currency == 'gems': await g.add(m.from_user.id, n, 'refund', f'host:{typ}')
            else: await e.add(m.from_user.id, n)
            return None, f'Could not create game: {ex}'

    async def join(m, typ, n, currency):
        group = await db.groups.find_one({'chat_id': m.chat.id})
        if group and group.get('gaming_open') is False:
            return None, 'Gaming commands are closed in this group. Use /open.'
        game = await db.games.find_one({'chat_id': m.chat.id, 'type': typ, 'status': 'joining'}, sort=[('created_at', -1)])
        if not game:
            return None, 'No open game.'
        if now() >= game['created_at'] + timedelta(seconds=JOIN_SECONDS):
            return None, 'Joining time is over.'
        if int(game['stake']) != int(n):
            return None, 'Stake must match the host.'
        if game['currency'] != currency:
            return None, f"This game uses {game['currency']} stakes."
        entries = await gm.entries(game['game_id'])
        maxp = int(game.get('data', {}).get('max_players', MAX_GAME_PLAYERS))
        if len(entries) >= maxp:
            return None, 'Game is full.'
        if any(x['user_id'] == m.from_user.id for x in entries):
            return None, 'You are already in this game.'
        await e.ensure(m.from_user.id, m.from_user.first_name, m.from_user.username)
        ok, msg = await stake(m.from_user.id, n, currency, game['game_id'])
        if not ok:
            return None, msg or 'Insufficient funds.'
        if not await gm.join(game['game_id'], m.from_user.id, n, currency):
            if currency == 'gems': await g.add(m.from_user.id, n, 'refund', game['game_id'])
            else: await e.add(m.from_user.id, n)
            return None, 'Already joined.'
        return game['game_id'], ''

    async def finish_pot(gid, winners, extra=None):
        if not isinstance(winners, (list, tuple, set)): winners = [winners]
        winners = list(dict.fromkeys(int(x) for x in winners))
        if not winners: return False
        async with gm.lock(gid):
            game = await gm.get(gid)
            if not game or game.get('status') != 'active': return False
            r = await db.games.update_one({'game_id': gid, 'status': 'active'},
                                          {'$set': {'status': 'finished', 'finished_at': now()}})
            if not r.modified_count: return False
            entries = await gm.entries(gid); pot = sum(int(x['stake']) for x in entries)
            currency = game.get('currency', 'coins')
            share, rem = divmod(pot, len(winners))
            for i, uid in enumerate(winners):
                award = share + (1 if i < rem else 0)
                if currency == 'gems': await g.add(uid, award, 'game_win', gid)
                else: await e.add(uid, award)
            data = dict(game.get('data') or {}); data.update(extra or {}); data['winners'] = winners; data['pot'] = pot
            await db.games.update_one({'game_id': gid}, {'$set': {'data': data}})
            return True

    async def send_dm(uid, text):
        try:
            await app.send_message(uid, text)
            return True
        except Exception:
            return False

    async def auto_finish_after_join(gid):
        await asyncio.sleep(JOIN_SECONDS)
        game = await gm.get(gid)
        if not game or game.get('status') != 'joining': return
        entries = await gm.entries(gid)
        if len(entries) < 2:
            await refund(gid); return
        await activate(gid)

    async def activate(gid):
        game = await gm.get(gid)
        if not game or game.get('status') != 'joining': return
        entries = await gm.entries(gid)
        if len(entries) < 2: return await refund(gid)
        data = dict(game.get('data') or {}); ids = [x['user_id'] for x in entries]; pot = sum(x['stake'] for x in entries)
        typ = game['type']
        if typ == 'hack':
            length = int(data['length']); data.update(password=''.join(str(random.randrange(10)) for _ in range(length)), players=ids, pot=pot, attempts={})
        elif typ == 'card':
            # Every player gets four 1..10 cards with exactly the same total.
            target_sum = random.randint(22, 30)
            hands = {}
            for uid in ids:
                while True:
                    cards = [random.randint(1,10) for _ in range(3)]
                    last = target_sum - sum(cards)
                    if 1 <= last <= 10:
                        cards.append(last); random.shuffle(cards); break
                hands[str(uid)] = cards
            data.update(hands=hands, round=0, scores={str(uid):0 for uid in ids}, used={}, picked={str(uid):[] for uid in ids}, round_deadline=(now().timestamp()+CARD_TURN_SECONDS))
        elif typ == 'bomb':
            data.update(alive=ids[:], turn=0, pot=pot, round=1, turn_deadline=now().timestamp()+45)
        elif typ == 'roulette':
            data.update(round=1, alive=ids[:], bids={}, pot=pot, bid_deadline=now().timestamp()+60)
        elif typ == 'bluff':
            hands = {str(uid): dict(zip('abcd', random.sample([1,2,3,4],4))) for uid in ids}
            data.update(hands=hands, turn=0, pile=[], required=random.randint(1,4), last_drop=None, pot=pot, turn_deadline=now().timestamp()+60)
        await db.games.update_one({'game_id':gid,'status':'joining'},{'$set':{'status':'active','data':data,'started_at':now()}})
        for uid in ids:
            if typ == 'card':
                h=data['hands'][str(uid)]; await send_dm(uid, f'🃏 <b>Viora Card</b>\nA={h[0]}  B={h[1]}  C={h[2]}  D={h[3]}\n\nUse /flip a|b|c|d in the group. Each round has {CARD_TURN_SECONDS}s.')
            elif typ == 'bluff':
                h=data['hands'][str(uid)]; await send_dm(uid, '🃏 <b>Viora Bluff</b>\nYour hidden hand: ' + ' '.join(f'{k.upper()}={v}' for k,v in h.items()) + '\nUse /drop a [b c d] on your turn.')
        if typ == 'card': tasks[gid] = asyncio.create_task(card_timer(gid))
        elif typ == 'bluff': tasks[gid] = asyncio.create_task(bluff_timer(gid))
        elif typ == 'roulette': tasks[gid] = asyncio.create_task(roulette_timer(gid))
        elif typ == 'bomb': tasks[gid] = asyncio.create_task(bomb_timer(gid))

    async def card_timer(gid):
        while True:
            game=await gm.get(gid)
            if not game or game.get('status')!='active': return
            d=game['data']; deadline=float(d.get('round_deadline',0)); await asyncio.sleep(max(.2,deadline-now().timestamp()))
            game=await gm.get(gid)
            if not game or game.get('status')!='active': return
            d=game['data']; ids=[x['user_id'] for x in await gm.entries(gid)]; used=d.setdefault('used',{}).setdefault(str(d['round']),{})
            for uid in ids:
                su=str(uid)
                if su not in used:
                    picked=d.setdefault('picked',{}).setdefault(su,[]); idx=next(i for i in range(4) if i not in picked); picked.append(idx); used[su]=idx
            await resolve_card(game,d,ids)

    async def resolve_card(game,d,ids):
        used=d['used'].setdefault(str(d['round']),{})
        if len(used)<len(ids): return
        vals={uid:d['hands'][str(uid)][idx] for uid,idx in used.items()}; high=max(vals.values()); total=sum(vals.values())
        for uid,v in vals.items():
            if v==high: d['scores'][uid]+=total
        d['round']+=1
        if d['round']>=4:
            best=max(d['scores'].values()); winners=[int(uid) for uid,v in d['scores'].items() if v==best]
            await finish_pot(game['game_id'],winners,{'reason':'card','scores':d['scores']}); return
        d['used'][str(d['round'])]={}; d['round_deadline']=now().timestamp()+CARD_TURN_SECONDS
        await db.games.update_one({'game_id':game['game_id'],'status':'active'},{'$set':{'data':d}})

    async def bluff_timer(gid):
        while True:
            game=await gm.get(gid)
            if not game or game.get('status')!='active': return
            d=game['data']; await asyncio.sleep(max(.2,float(d.get('turn_deadline',0))-now().timestamp()))
            game=await gm.get(gid)
            if not game or game.get('status')!='active': return
            d=game['data']; ids=[x['user_id'] for x in await gm.entries(gid)]; uid=ids[d['turn']%len(ids)]; hand=d['hands'].get(str(uid),{})
            if hand:
                card=next(iter(hand)); await do_drop(game,d,uid,[card],auto=True)
            else:
                await finish_pot(gid,uid,{'reason':'bluff_empty'})

    async def do_drop(game,d,uid,cards,auto=False):
        hand=d['hands'].get(str(uid),{})
        if any(x not in hand for x in cards): return False,'Card unavailable.'
        vals=[hand[x] for x in cards]
        for x in cards: hand.pop(x,None)
        d['pile'].extend(vals); d['last_drop']={'uid':uid,'cards':cards,'values':vals,'truth':all(v==d['required'] for v in vals)}
        if not hand:
            await finish_pot(game['game_id'],uid,{'reason':'bluff_empty'}); return True,'🏆 You emptied your hand and won!'
        d['turn']=(d['turn']+1)%len((await gm.entries(game['game_id']))); d['turn_deadline']=now().timestamp()+60
        await db.games.update_one({'game_id':game['game_id'],'status':'active'},{'$set':{'data':d}})
        return True,'🃏 Cards dropped. Next player may /judge or /drop.'

    async def roulette_timer(gid):
        while True:
            game=await gm.get(gid)
            if not game or game.get('status')!='active': return
            d=game['data']; await asyncio.sleep(max(.2,float(d.get('bid_deadline',0))-now().timestamp()))
            game=await gm.get(gid)
            if not game or game.get('status')!='active': return
            d=game['data']; alive=d['alive']; bids=d.setdefault('bids',{}); current=[int(v) for v in bids.values()]
            for uid in alive:
                if str(uid) not in bids: bids[str(uid)] = 0
            low=min(int(bids[str(uid)]) for uid in alive); losers=[uid for uid in alive if int(bids[str(uid)])==low]; loser=random.choice(losers); alive.remove(loser)
            if len(alive)==1:
                await finish_pot(gid,alive[0],{'reason':'roulette','round':d['round']}); return
            d['round']+=1; d['bids']={}; d['bid_deadline']=now().timestamp()+60
            await db.games.update_one({'game_id':gid,'status':'active'},{'$set':{'data':d}})

    async def bomb_timer(gid):
        while True:
            game = await gm.get(gid)
            if not game or game.get('status') != 'active': return
            d = game['data']; alive = d.get('alive', [])
            if len(alive) <= 1:
                if alive: await finish_pot(gid, alive[0], {'reason':'bomb'})
                return
            deadline = float(d.get('turn_deadline', 0))
            if deadline <= 0:
                deadline = now().timestamp() + 45
                d['turn_deadline'] = deadline
                await db.games.update_one({'game_id':gid,'status':'active'},{'$set':{'data':d}})
            await asyncio.sleep(max(.2, deadline - now().timestamp()))
            game = await gm.get(gid)
            if not game or game.get('status') != 'active': return
            d = game['data']; alive = d.get('alive', [])
            if len(alive) <= 1:
                if alive: await finish_pot(gid, alive[0], {'reason':'bomb'})
                return
            holder = alive[d.get('turn',0) % len(alive)]
            alive.remove(holder)
            if len(alive) == 1:
                await finish_pot(gid, alive[0], {'reason':'bomb','exploded_user':holder})
                return
            d['turn'] %= len(alive); d['round'] = d.get('round',1) + 1; d['turn_deadline'] = now().timestamp() + 45
            await db.games.update_one({'game_id':gid,'status':'active'},{'$set':{'data':d}})
            try: await app.send_message(game['chat_id'], f'💥 <a href="tg://user?id={holder}">Player</a> was hit by the bomb! {len(alive)} remain.')
            except Exception: pass


    async def recover():
        # Rebuild in-memory timers after a Render restart. Joining games are resumed or settled immediately.
        rows = await db.games.find({'status': {'$in':['joining','active']}}).to_list(500)
        for game in rows:
            gid = game['game_id']
            if game['status'] == 'joining':
                age = (now() - game['created_at']).total_seconds()
                if age >= JOIN_SECONDS:
                    entries = await gm.entries(gid)
                    if len(entries) >= 2: await activate(gid)
                    else: await refund(gid)
                else:
                    async def resume_join(g=gid, delay=JOIN_SECONDS-age):
                        await asyncio.sleep(max(0, delay))
                        game2 = await gm.get(g)
                        if not game2 or game2.get('status') != 'joining': return
                        entries2 = await gm.entries(g)
                        if len(entries2) >= 2: await activate(g)
                        else: await refund(g)
                    asyncio.create_task(resume_join())
            elif game['status'] == 'active':
                typ = game.get('type')
                if typ == 'card': tasks[gid] = asyncio.create_task(card_timer(gid))
                elif typ == 'bluff': tasks[gid] = asyncio.create_task(bluff_timer(gid))
                elif typ == 'roulette': tasks[gid] = asyncio.create_task(roulette_timer(gid))
                elif typ == 'bomb': tasks[gid] = asyncio.create_task(bomb_timer(gid))
    app.viora_recover = recover

    @app.on_message(filters.command('hack') & filters.group)
    async def hack(_,m):
        if len(m.command)<3:return await m.reply('/hack <amount> <password_length>')
        try:n,length=amount(m.command[1]),int(m.command[2]); cur=(m.command[3] if len(m.command)>3 else 'coins').lower()
        except: return await m.reply('❌ Invalid arguments.')
        if cur not in ('coins','gems') or not 3<=length<=6:return await m.reply('❌ Length must be 3-6 and currency coins/gems.')
        gid,err=await create(m,'hack',n,cur,{'length':length});
        if gid: asyncio.create_task(auto_finish_after_join(gid)); await m.reply(f'🧠 Hack lobby <code>{gid}</code>\n/register {n} {cur}')
        else: await m.reply('❌ '+err)

    @app.on_message(filters.command('register'))
    async def register(_,m):
        if len(m.command)<2:return await m.reply('/register <amount> <coins|gems>')
        try:n=amount(m.command[1]);cur=(m.command[2] if len(m.command)>2 else 'coins').lower()
        except:return await m.reply('❌ Invalid.')
        gid,err=await join(m,'hack',n,cur); await m.reply('✅ Registered.' if gid else '❌ '+err)

    @app.on_message(filters.command('guess') & filters.group)
    async def guess(_,m):
        game=await db.games.find_one({'chat_id':m.chat.id,'type':'hack','status':'active'},sort=[('created_at',-1)])
        if not game:return await m.reply('❌ No active hack.')
        if len(m.command)<2:return await m.reply('/guess <password>')
        ids=[x['user_id'] for x in await gm.entries(game['game_id'])]
        if m.from_user.id not in ids:return await m.reply('❌ You are not registered.')
        pw=game['data']['password']; val=m.command[1].strip()
        if len(val)!=len(pw) or not val.isdigit():return await m.reply(f'❌ Password must be {len(pw)} digits.')
        hits=sum(a==b for a,b in zip(pw,val)); common=sum(min(val.count(ch),pw.count(ch)) for ch in set(val)); glitches=common-hits
        await m.reply(f'🎯 Hacks: {hits}\n⚡ Glitches: {glitches}\n❌ Absent: {len(pw)-hits-glitches}')
        if val==pw and await finish_pot(game['game_id'],m.from_user.id,{'reason':'hack'}): await m.reply('🏆 Correct password! You won the pot.')

    @app.on_message(filters.command('bluff') & filters.group)
    async def bluff(_,m):
        if len(m.command)<3:return await m.reply('/bluff <amount> <players> [coins|gems]')
        try:n,p=amount(m.command[1]),int(m.command[2]);cur=(m.command[3] if len(m.command)>3 else 'coins').lower()
        except:return await m.reply('❌ Invalid.')
        if cur not in ('coins','gems') or not 2<=p<=MAX_GAME_PLAYERS:return await m.reply('❌ Invalid player count/currency.')
        gid,err=await create(m,'bluff',n,cur,{'max_players':p});
        if gid:asyncio.create_task(auto_finish_after_join(gid));await m.reply(f'🃏 Bluff lobby {gid}\n/enter {n} {cur}')
        else:await m.reply('❌ '+err)

    @app.on_message(filters.command('enter'))
    async def enter(_,m):
        if len(m.command)<2:return await m.reply('/enter <amount> <coins|gems>')
        try:n=amount(m.command[1]);cur=(m.command[2] if len(m.command)>2 else 'coins').lower()
        except:return await m.reply('❌ Invalid.')
        gid,err=await join(m,'bluff',n,cur);await m.reply('✅ Entered bluff.' if gid else '❌ '+err)

    @app.on_message(filters.command('drop') & filters.group)
    async def drop(_,m):
        game=await db.games.find_one({'chat_id':m.chat.id,'type':'bluff','status':'active'},sort=[('created_at',-1)])
        if not game:return await m.reply('❌ No active bluff.')
        d=game['data'];ids=[x['user_id'] for x in await gm.entries(game['game_id'])]
        if ids[d['turn']%len(ids)]!=m.from_user.id:return await m.reply('⏳ Not your turn.')
        cards=[x.lower() for x in m.command[1:]]
        if not cards or any(x not in 'abcd' for x in cards) or len(set(cards))!=len(cards):return await m.reply('/drop a [b c d]')
        ok,msg=await do_drop(game,d,m.from_user.id,cards);await m.reply(msg)

    @app.on_message(filters.command('judge') & filters.group)
    async def judge(_,m):
        game=await db.games.find_one({'chat_id':m.chat.id,'type':'bluff','status':'active'},sort=[('created_at',-1)])
        if not game:return await m.reply('❌ No active bluff.')
        d=game['data'];last=d.get('last_drop');ids=[x['user_id'] for x in await gm.entries(game['game_id'])]
        if not last:return await m.reply('❌ Nothing to judge.')
        if m.from_user.id==last['uid'] or m.from_user.id not in ids:return await m.reply('❌ Only the next player can judge.')
        judge_id=m.from_user.id; hand=d['hands'][str(judge_id)]
        pile=list(d.get('pile',[]))
        # Both outcomes award the table pile to the judge; the penalty differs.
        # If the claim was false, the judge was correct and loses one card.
        if not last['truth']:
            if hand: hand.pop(random.choice(list(hand.keys())))
            msg='✅ Correct judge. The claim was false; you take the pile and lose one card.'
        else:
            msg='❌ Wrong judge. The claim was true; you take the table pile.'
        for value in pile:
            label=next((x for x in 'abcd' if x not in hand),None)
            if label: hand[label]=value
        d['pile']=[]; d['hands'][str(judge_id)]=hand; d['last_drop']=None; d['turn']=ids.index(judge_id); d['turn_deadline']=now().timestamp()+60
        if not hand:
            await finish_pot(game['game_id'],judge_id,{'reason':'bluff_empty_after_judge'}); return await m.reply('🏆 You have no cards left and win!')
        await db.games.update_one({'game_id':game['game_id'],'status':'active'},{'$set':{'data':d}});await m.reply(msg)

    @app.on_message(filters.command('roulette') & filters.group)
    async def roulette(_,m):
        if len(m.command)<3:return await m.reply('/roulette <amount> <players_count/all> [coins|gems]')
        try:n=amount(m.command[1]);p=m.command[2].lower();cur=(m.command[3] if len(m.command)>3 else 'coins').lower();maxp=MAX_GAME_PLAYERS if p=='all' else int(p)
        except:return await m.reply('❌ Invalid.')
        if cur not in ('coins','gems') or not 2<=maxp<=MAX_GAME_PLAYERS:return await m.reply('❌ Invalid player count/currency.')
        gid,err=await create(m,'roulette',n,cur,{'max_players':maxp});
        if gid:asyncio.create_task(auto_finish_after_join(gid));await m.reply(f'🎰 Roulette lobby {gid}\n/join {n} {cur}\nThen /bid <amount> each round.')
        else:await m.reply('❌ '+err)

    @app.on_message(filters.command('join'))
    async def join_cmd(_,m):
        if len(m.command)<2:return await m.reply('/join <amount> <coins|gems>')
        try:n=amount(m.command[1]);cur=(m.command[2] if len(m.command)>2 else 'coins').lower()
        except:return await m.reply('❌ Invalid.')
        # /join is reserved for roulette/bomb; prefer latest open game.
        game=await db.games.find_one({'chat_id':m.chat.id,'status':'joining','type':{'$in':['roulette','bomb']}},sort=[('created_at',-1)])
        if not game:return await m.reply('❌ No open roulette/bomb game.')
        gid,err=await join(m,game['type'],n,cur);await m.reply('✅ Joined.' if gid else '❌ '+err)

    @app.on_message(filters.command('bid'))
    async def bid(_,m):
        if m.chat.type != 'private': return await m.reply('📩 Send /bid in your private chat with Viora.')
        if m.chat.type == 'private':
            entry = await db.game_entries.find_one({'user_id':m.from_user.id})
            game = await db.games.find_one({'game_id': entry['game_id'], 'type':'roulette','status':'active'}) if entry else None
        else:
            game=await db.games.find_one({'chat_id':m.chat.id,'type':'roulette','status':'active'},sort=[('created_at',-1)])
        if not game:return await m.reply('❌ No active roulette.')
        if len(m.command)<2:return await m.reply('/bid <amount>')
        try:n=amount(m.command[1])
        except:return await m.reply('❌ Invalid bid.')
        d=game['data'];alive=d['alive'];uid=m.from_user.id
        if uid not in alive:return await m.reply('❌ You are eliminated.')
        if n<=max([int(v) for v in d.get('bids',{}).values()] or [0]):return await m.reply('❌ Bid must be higher than the current highest bid.')
        d.setdefault('bids',{})[str(uid)]=n;await db.games.update_one({'game_id':game['game_id'],'status':'active'},{'$set':{'data':d}})
        if len(d['bids'])==len(alive):
            low=min(int(d['bids'][str(x)]) for x in alive);losers=[x for x in alive if int(d['bids'][str(x)])==low];alive.remove(random.choice(losers))
            if len(alive)==1:await finish_pot(game['game_id'],alive[0],{'reason':'roulette'});return await m.reply('🏆 Roulette winner!')
            d['round']+=1;d['bids']={};d['bid_deadline']=now().timestamp()+60;await db.games.update_one({'game_id':game['game_id'],'status':'active'},{'$set':{'data':d}})
            await m.reply(f'🎰 Round {d["round"]}: bid again. Lowest bid is eliminated.')
        else:await m.reply('✅ Bid recorded.')

    @app.on_message(filters.command('card') & filters.group)
    async def card(_,m):
        if len(m.command)<3:return await m.reply('/card <amount> <players> [coins|gems]')
        try:n,p=amount(m.command[1]),int(m.command[2]);cur=(m.command[3] if len(m.command)>3 else 'coins').lower()
        except:return await m.reply('❌ Invalid.')
        if cur not in ('coins','gems') or not 2<=p<=MAX_GAME_PLAYERS:return await m.reply('❌ Invalid.')
        gid,err=await create(m,'card',n,cur,{'max_players':p});
        if gid:asyncio.create_task(auto_finish_after_join(gid));await m.reply(f'🃏 Card lobby {gid}\n/bet {n} {cur}')
        else:await m.reply('❌ '+err)

    @app.on_message(filters.command('bet'))
    async def bet(_,m):
        if len(m.command)<2:return await m.reply('/bet <amount> <coins|gems>')
        try:n=amount(m.command[1]);cur=(m.command[2] if len(m.command)>2 else 'coins').lower()
        except:return await m.reply('❌ Invalid.')
        game=await db.games.find_one({'chat_id':m.chat.id,'status':'joining','type':'card'},sort=[('created_at',-1)])
        if not game:return await m.reply('❌ No open card game.')
        gid,err=await join(m,'card',n,cur);await m.reply('✅ Joined card game.' if gid else '❌ '+err)

    @app.on_message(filters.command('flip') & filters.group)
    async def flip(_,m):
        game=await db.games.find_one({'chat_id':m.chat.id,'type':'card','status':'active'},sort=[('created_at',-1)])
        if not game:return await m.reply('❌ No active card game.')
        if len(m.command)<2:return await m.reply('/flip a|b|c|d')
        d=game['data'];ids=[x['user_id'] for x in await gm.entries(game['game_id'])];uid=str(m.from_user.id)
        if uid not in d['hands']:return await m.reply('❌ You are not in this game.')
        idx={'a':0,'b':1,'c':2,'d':3}.get(m.command[1].lower());
        if idx is None:return await m.reply('/flip a|b|c|d')
        picked=d.setdefault('picked',{}).setdefault(uid,[]);used=d.setdefault('used',{}).setdefault(str(d['round']),{})
        if idx in picked:return await m.reply('❌ You already used that card.')
        if uid in used:return await m.reply('❌ Already flipped this round.')
        used[uid]=idx;picked.append(idx);await db.games.update_one({'game_id':game['game_id'],'status':'active'},{'$set':{'data':d}});await resolve_card(game,d,ids)
        await m.reply(f'🃏 {m.command[1].upper()} = {d["hands"][uid][idx]}')

    @app.on_message(filters.command('bomb') & filters.group)
    async def bomb(_,m):
        if len(m.command)<2:return await m.reply('/bomb <amount> [coins|gems]')
        try:n=amount(m.command[1]);cur=(m.command[2] if len(m.command)>2 else 'coins').lower()
        except:return await m.reply('❌ Invalid.')
        if cur not in ('coins','gems'):return await m.reply('❌ Currency must be coins or gems.')
        gid,err=await create(m,'bomb',n,cur,{'max_players':MAX_GAME_PLAYERS});
        if gid:asyncio.create_task(auto_finish_after_join(gid));await m.reply(f'💣 Bomb lobby {gid}\n/join {n} {cur}\n/pass to pass the bomb.')
        else:await m.reply('❌ '+err)

    @app.on_message(filters.command('pass') & filters.group)
    async def pass_bomb(_,m):
        game=await db.games.find_one({'chat_id':m.chat.id,'type':'bomb','status':'active'},sort=[('created_at',-1)])
        if not game:return await m.reply('❌ No bomb game.')
        d=game['data'];alive=d['alive'];uid=m.from_user.id
        if uid not in alive:return await m.reply('💀 You are out.')
        if alive[d['turn']%len(alive)]!=uid:return await m.reply('⏳ Not your turn.')
        # Random explosion occurs on a pass, with an increasing but bounded chance.
        chance=min(.15 + d.get('round',1)*.03,.50)
        if random.random()<chance:
            alive.remove(uid)
            if len(alive)==1:
                await finish_pot(game['game_id'],alive[0],{'reason':'bomb'});return await m.reply('💥 Bomb exploded! 🏆 Last survivor wins!')
            d['round']+=1;d['turn']%=len(alive);d['turn_deadline']=now().timestamp()+45
            await db.games.update_one({'game_id':game['game_id'],'status':'active'},{'$set':{'data':d}});return await m.reply(f'💥 Bomb exploded! {len(alive)} players remain.')
        d['turn']=(d['turn']+1)%len(alive);d['round']+=1;d['turn_deadline']=now().timestamp()+45
        await db.games.update_one({'game_id':game['game_id'],'status':'active'},{'$set':{'data':d}});await m.reply(f'➡️ Passed safely. {len(alive)} alive.')

    @app.on_message(filters.command(['rank','leaders']))
    async def bomb_leaders(_,m):
        rows=await db.games.find({'type':'bomb','status':'finished'}).to_list(500);counts={}
        for row in rows:
            for uid in row.get('data',{}).get('winners',[]):counts[uid]=counts.get(uid,0)+1
        out=sorted(counts.items(),key=lambda x:x[1],reverse=True)[:10];await m.reply('💣 Bomb Leaders\n'+('\n'.join(f'{i}. <code>{uid}</code> — {n}' for i,(uid,n) in enumerate(out,1)) or 'No winners yet.'))

    @app.on_message(filters.command('end') & filters.group)
    async def end(_,m):
        game=await db.games.find_one({'chat_id':m.chat.id,'status':{'$in':['joining','active']},'host_id':m.from_user.id})
        if not game:return await m.reply('❌ Only the host can end their active game.')
        await refund(game['game_id']);await m.reply('🛑 Game ended and all stakes were refunded.')

    @app.on_message(filters.command('bombcancel') & filters.group)
    async def bombcancel(_,m):
        allowed=m.from_user.id in OWNER_IDS
        if not allowed:
            try:
                member=await app.get_chat_member(m.chat.id,m.from_user.id);allowed=bool(member.privileges and member.privileges.can_manage_chat)
            except Exception:allowed=False
        if not allowed:return await m.reply('❌ Admin only.')
        game=await db.games.find_one({'chat_id':m.chat.id,'type':'bomb','status':{'$in':['joining','active']}})
        if game and await refund(game['game_id']):await m.reply('🛑 Bomb cancelled and refunded.')
        else:await m.reply('❌ No active bomb game.')
