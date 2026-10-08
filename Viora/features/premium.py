from pyrogram import filters
from pyrogram.raw.types import UpdateBotPrecheckoutQuery
from pyrogram.raw.functions.messages import SetBotPrecheckoutResults
from Viora.config import PREMIUM_STARS, PREMIUM_DAYS

async def register(app, c):
    api = c['api']; p = c['premium']; e = c['economy']; db = c['db']

    @app.on_message(filters.command(['pay', 'premium']))
    async def pay(_, m):
        await api.invoice(
            m.from_user.id,
            'Viora Premium',
            f'{PREMIUM_DAYS} days Premium',
            'premium:' + str(m.from_user.id),
            'XTR',
            [{'label': f'Premium {PREMIUM_DAYS} days', 'amount': PREMIUM_STARS}],
            ''
        )

    @app.on_message(filters.command('setemoji'))
    async def setemoji(_, m):
        if not await p.active(m.from_user.id):
            return await m.reply('👑 Premium only.')
        if len(m.command) < 2:
            return await m.reply('/setemoji <emoji>')
        await e.ensure(m.from_user.id, m.from_user.first_name, m.from_user.username)
        emoji = m.command[1].strip()
        if len(emoji) > 16:
            return await m.reply('❌ Emoji is too long.')
        await e.c.update_one({'user_id': m.from_user.id}, {'$set': {'emoji': emoji}})
        await m.reply('✅ Custom emoji saved.')

    # Pyrogram 2.x does not expose on_pre_checkout_query().
    # Handle Telegram's raw pre-checkout update directly and answer within Telegram's 10s window.
    @app.on_raw_update()
    async def precheckout(client, update, users, chats):
        if isinstance(update, UpdateBotPrecheckoutQuery):
            await client.invoke(SetBotPrecheckoutResults(
                query_id=update.query_id,
                success=True
            ))

    # Pyrogram has no built-in successful_payment filter in this runtime.
    payment_filter = filters.create(
        lambda _, __, message: bool(getattr(message, 'successful_payment', None))
    )

    @app.on_message(payment_filter)
    async def paid(_, m):
        sp = m.successful_payment
        payload = sp.invoice_payload or ''
        if not payload.startswith('premium:'):
            return
        charge = sp.telegram_payment_charge_id
        try:
            await db.payments.insert_one({
                'charge_id': charge,
                'uid': m.from_user.id,
                'payload': payload,
                'kind': 'premium'
            })
        except Exception:
            # Unique charge_id makes repeated Telegram delivery idempotent.
            return
        await p.grant(m.from_user.id, PREMIUM_DAYS)
        await m.reply('👑 Premium activated!')
