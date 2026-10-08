from pyrogram import filters
async def register(app,c):
 e=c['economy']; api=c['api']
 @app.on_message(filters.command('start'))
 async def start(_,m):
  u=await e.ensure(m.from_user.id,m.from_user.first_name,m.from_user.username); rank=await c['leader'].rank(m.from_user.id)
  kb=api.kb((api.btn('🍀 VIORA FEATURES','menu:features',style='primary'),api.btn('🎮 GAMES','menu:games',style='primary')),(api.btn('👥 GROUPS','menu:groups',style='primary'),api.btn('💸 PROMOTER','menu:promoter',style='primary')),(api.btn('📢 UPDATES','menu:updates',style='primary'),api.btn('➕ ADD ME TO YOUR GROUP',f'https://t.me/{c["config"].BOT_USERNAME}?startgroup=true',style='success')))
  await api.send(m.chat.id,f"🌸 <b>Welcome to Viora</b>\n\n💰 Balance: <b>${u['balance']:,}</b>\n🏆 Rank: <b>#{rank}</b>\n💎 Gems: <b>{u.get('gems',0)//1000}</b>\n🔪 Kills: <b>{u.get('kills',0)}</b>\n\n<b>HOW TO PLAY</b>\n/bal — check balance\n/pfp — profile\n/daily — daily reward\n/protect — protect your balance\n/kill & /rob — compete\n\nChoose a section below.",kb)
