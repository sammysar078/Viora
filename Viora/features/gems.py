from pyrogram import filters
from Viora.config import GEM_PRICE_INR

async def register(app, c):
    e, g, api, db = c['economy'], c['gems'], c['api'], c['db']

    @app.on_message(filters.command('gems'))
    async def gems(_, m):
        if len(m.command) > 1:
            # /gems <amount> is the purchase shortcut; /buygems remains available too.
            try: n = int(m.command[1]); assert 1 <= n <= 1000000000
            except Exception: return await m.reply('❌ Invalid gem amount.')
            token = c['config'].PAYMENT_PROVIDER_TOKEN
            if not token: return await m.reply('❌ Gem payment provider is not configured on this bot.')
            payload=f'gems:{m.from_user.id}:{n}'
            return await api.invoice(m.from_user.id,'Viora Gems',f'{n} gems',payload,'INR',[{'label':f'{n} Gems','amount':n*GEM_PRICE_INR*100}],token)
        u = await e.ensure(m.from_user.id, m.from_user.first_name, m.from_user.username)
        n = int(u.get('gems', 0)) // 1000
        await m.reply(f'💎 <b>Gems</b>: {n}\n1 gem = $10,000 coins = ₹{GEM_PRICE_INR}.\nPremium users can use up to 50 gems/day.')

    @app.on_message(filters.command('convert'))
    async def convert(_, m):
        if len(m.command) < 2: return await m.reply('/convert <gems>')
        try: n = int(m.command[1]); assert n > 0
        except Exception: return await m.reply('❌ Invalid gem amount.')
        ok, msg = await g.convert(m.from_user.id, n)
        await m.reply('✅ Converted to coins.' if ok else '❌ ' + msg)

    @app.on_message(filters.command('buygems'))
    async def buy(_, m):
        if len(m.command) < 2: return await m.reply('/buygems <gems>')
        try: n = int(m.command[1]); assert 1 <= n <= 1000000000
        except Exception: return await m.reply('❌ Invalid gem amount.')
        token = c['config'].PAYMENT_PROVIDER_TOKEN
        if not token: return await m.reply('❌ Gem payment provider is not configured on this bot.')
        payload = f'gems:{m.from_user.id}:{n}'
        await api.invoice(m.from_user.id, 'Viora Gems', f'{n} gems', payload, 'INR',
                          [{'label': f'{n} Gems', 'amount': n * GEM_PRICE_INR * 100}], token)

    @app.on_message(filters.successful_payment)
    async def gem_paid(_, m):
        sp = m.successful_payment
        payload = sp.invoice_payload or ''
        if not payload.startswith('gems:'): return
        charge = sp.telegram_payment_charge_id
        try:
            await db.payments.insert_one({'charge_id': charge, 'uid': m.from_user.id, 'payload': payload, 'kind': 'gems'})
        except Exception:
            # Unique charge_id makes this idempotent.
            return
        try:
            _, uid, n = payload.split(':', 2)
            uid, n = int(uid), int(n)
        except Exception:
            return
        if uid != m.from_user.id: return
        await g.add(uid, n, 'purchase', charge)
        await m.reply(f'💎 Payment successful. {n} gems added to your account.')
