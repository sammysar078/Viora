from pyrogram import filters
from Viora.config import *
from Viora.core.common import *
async def register(app,c):
 e=c['economy']
 @app.on_message(filters.command(['bal','balance']))
 async def bal(_,m):
  u=await e.ensure(m.from_user.id,m.from_user.first_name,m.from_user.username); await c['api'].send(m.chat.id,f"💰 <b>Balance</b>\nCash: <b>{money(u['balance'])}</b>\nWallet: <b>{money(u['wallet'])}</b>",reply_to=m.id)
 @app.on_message(filters.command('pfp'))
 async def pfp(_,m):
  u=await e.ensure(m.from_user.id,m.from_user.first_name,m.from_user.username); prem=await e.premium(u); rank=await c['leader'].rank(m.from_user.id); emoji=u.get('emoji') or ('❤️' if prem else '👤')
  await c['api'].send(m.chat.id,f"{emoji} <b>{mention(m.from_user)}</b>\n💰 {money(u['balance'])} | 🏦 {money(u['wallet'])}\n💎 {u.get('gems',0)//1000}\n🔪 Kills: {u.get('kills',0)}\n🦹 Robs: {u.get('robs',0)}\n⭐ XP: {u.get('xp',0)} | Rank #{rank}\n👑 Premium: {'Yes' if prem else 'No'}",reply_to=m.id)
 @app.on_message(filters.command('daily'))
 async def daily(_,m):
  u=await e.ensure(m.from_user.id,m.from_user.first_name,m.from_user.username); prem=await e.premium(u)
  if prem:
   ok,coins,xp=await e.daily_reward(m.from_user.id,True); return await m.reply(f"🎁 Daily claimed: <b>{money(coins)}</b> + <b>{xp} XP</b>" if ok else '⏳ You already claimed your daily reward today.')
  kb=c['api'].kb((c['api'].btn('✅ VERIFY & CLAIM',f'daily:verify:{m.from_user.id}',style='success'),))
  await c['api'].send(m.chat.id,'🔐 <b>Daily verification</b>\nPress the button below to claim your normal daily reward of $2,000 + 50 XP.',kb,reply_to=m.id)
 @app.on_callback_query(filters.regex(r'^daily:verify:\d+$'))
 async def daily_verify(_,q):
  try: owner=int(q.data.rsplit(':',1)[1])
  except Exception: return await c['api'].answer(q.id,'Invalid verification.',True)
  if owner!=q.from_user.id: return await c['api'].answer(q.id,'This verification belongs to another user.',True)
  u=await e.ensure(q.from_user.id,q.from_user.first_name,q.from_user.username); ok,coins,xp=await e.daily_reward(q.from_user.id,await e.premium(u)); await c['api'].answer(q.id,'Claimed!' if ok else 'Already claimed today.')
  if ok: await q.message.reply(f"🎁 Daily claimed: <b>{money(coins)}</b> + <b>{xp} XP</b>")
 @app.on_message(filters.command('kill') & filters.reply)
 async def kill(_,m):
  if m.chat.type in ('group','supergroup'):
   group=await c['db'].groups.find_one({'chat_id':m.chat.id})
   if group and group.get('gaming_open') is False: return await m.reply('🔒 Gaming commands are closed in this group. Use /open.')
  u=await e.ensure(m.from_user.id,m.from_user.first_name,m.from_user.username); t=m.reply_to_message.from_user
  if u.get('dead'): return await m.reply('💀 You are dead. Use /revive first.')
  if t.id==m.from_user.id or t.is_bot: return await m.reply('❌ Invalid target.')
  target=await e.ensure(t.id,t.first_name,t.username)
  if target.get('dead'): return await m.reply('💀 This user is already dead. Use /revive first.')
  ok=await e.kill(m.from_user.id,await e.premium(u))
  if ok: await e.c.update_one({'user_id':t.id},{'$set':{'dead':True}}); await m.reply(f"🔪 {mention(m.from_user)} killed {mention(t)} and earned {money(ok[0])} + {ok[1]} XP.")
  else: await m.reply('🚫 Daily kill limit reached.')
 @app.on_message(filters.command('rob') & filters.reply)
 async def rob(_,m):
  if m.chat.type in ('group','supergroup'):
   group=await c['db'].groups.find_one({'chat_id':m.chat.id})
   if group and group.get('gaming_open') is False: return await m.reply('🔒 Gaming commands are closed in this group. Use /open.')
  if len(m.command)<2:return await m.reply('Usage: /rob <amount>')
  try:n=amount(m.command[1])
  except:return await m.reply('❌ Invalid amount.')
  u=await e.ensure(m.from_user.id,m.from_user.first_name,m.from_user.username); t=m.reply_to_message.from_user
  if t.id==m.from_user.id or t.is_bot:return await m.reply('❌ Invalid target.')
  await e.ensure(t.id,t.first_name,t.username)
  if u.get('dead'): return await m.reply('💀 You are dead. Use /revive first.')
  prem=await e.premium(u); maxn=PREMIUM_ROB_MAX if prem else NORMAL_ROB_MAX
  if n>maxn:return await m.reply(f'❌ Your rob limit is {money(maxn)}.')
  status,res=await e.rob(m.from_user.id,t.id,prem,n)
  if status=='ok':
   stolen,xp=res; await m.reply(f'💸 {mention(m.from_user)} robbed {money(stolen)} from {mention(t)} + {xp} XP.')
  elif status=='protected': await m.reply('🛡️ Target is protected.')
  elif status=='cloaked': await m.reply('🥷 Target is cloaked. The robbery failed.')
  elif status=='limit': await m.reply('🚫 Daily rob limit reached.')
  else: await m.reply('💸 Target has no rob-able cash.')
 @app.on_message(filters.command('give') & filters.reply)
 async def give(_,m):
  if len(m.command)<2:return await m.reply('Usage: /give <amount>')
  try:n=amount(m.command[1])
  except:return await m.reply('❌ Invalid amount.')
  me=await e.ensure(m.from_user.id)
  if me.get('dead'): return await m.reply('💀 You are dead. Use /revive first.')
  prem=await e.premium(me); tax=PREMIUM_TAX if prem else NORMAL_TAX; t=m.reply_to_message.from_user; await e.ensure(t.id,t.first_name,t.username); ok,recv=await e.transfer(m.from_user.id,t.id,n,tax); await m.reply(f"✅ Sent {money(recv)} after {int(tax*100)}% tax." if ok else '❌ Not enough balance.')
 @app.on_message(filters.command('wallet'))
 async def wallet(_,m):
  if len(m.command)<3:return await m.reply('Usage: /wallet <deposit|withdraw> <amount>')
  try:n=amount(m.command[2])
  except:return await m.reply('❌ Invalid amount.')
  await e.ensure(m.from_user.id); ok=await e.wallet(m.from_user.id,m.command[1].lower(),n); await m.reply('✅ Wallet updated.' if ok else '❌ Insufficient funds.')
 @app.on_message(filters.command('protect'))
 async def protect(_,m):
  try:
   raw=m.command[1].lower().strip(); d=int(raw[:-1] if raw.endswith('d') else raw)
  except:return await m.reply('Usage: /protect 1d or /protect 2d')
  u=await e.ensure(m.from_user.id); ok,cost=await e.protect(m.from_user.id,await e.premium(u),d); await m.reply(f'🛡️ Protection active for {d} day(s). Cost {money(cost)}.' if ok else '❌ Not enough balance.')
 @app.on_message(filters.command('revive'))
 async def revive(_,m):
  t=m.reply_to_message.from_user.id if m.reply_to_message and m.reply_to_message.from_user else m.from_user.id; await e.ensure(t); await m.reply('❤️ Revived.' if await e.revive(m.from_user.id,t) else '❌ User is not dead.')
 @app.on_message(filters.command('check') & filters.reply)
 async def check(_,m):
  u=await e.ensure(m.reply_to_message.from_user.id); prem=await e.premium(await e.ensure(m.from_user.id));
  if not prem:return await m.reply('👑 Premium only.')
  p=u.get('protection_until'); await m.reply('🛡️ Protected: '+human((p-now()).total_seconds()) if p and p>now() else '❌ Not protected.')
 @app.on_message(filters.command('toprich'))
 async def top_rich(_,m):
  rows=await c['leader'].rich(); lines=[]
  for i,x in enumerate(rows,1):
   badge=' 👑' if await e.premium(x) else ''
   lines.append(f"{i}. {x.get('name','User')}{badge} — {money(x.get('balance',0))}")
  await m.reply('🏆 <b>Top Rich</b>\n'+'\n'.join(lines))
 @app.on_message(filters.command('topkill'))
 async def top_kill(_,m):
  rows=await c['leader'].kills(); lines=[]
  for i,x in enumerate(rows,1):
   badge=' 👑' if await e.premium(x) else ''
   lines.append(f"{i}. {x.get('name','User')}{badge} — {x.get('kills',0)}")
  await m.reply('🔪 <b>Top Killers</b>\n'+'\n'.join(lines))
 @app.on_message(filters.command('economy'))
 async def eco(_,m): await m.reply('💰 Viora Economy lets you earn coins, protect them, rob rivals, kill targets, use a wallet, compete on leaderboards and spend gems in games. Premium improves limits and rewards.')
