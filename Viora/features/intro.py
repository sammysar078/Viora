from pyrogram import filters
from Viora.core.common import target_from_reply,mention
async def register(app,c):
 e=c['economy']
 @app.on_message(filters.command('setintro'))
 async def seti(_,m):
  text=' '.join(m.command[1:]);
  if not text:return await m.reply('/setintro <text>')
  await e.c.update_one({'user_id':m.from_user.id},{'$set':{'intro':text}}); await m.reply('✅ Intro saved.')
 @app.on_message(filters.command('intro'))
 async def intro(_,m):
  t=target_from_reply(m) or m.from_user; u=await e.ensure(t.id,t.first_name,t.username); await m.reply(f'📝 <b>{mention(t)}</b>\n{u.get("intro") or "No intro set."}')
