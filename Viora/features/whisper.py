import re
from pyrogram import filters
async def register(app,c):
 api=c['api']; e=c['economy']
 async def send(target,text,m):
  try: await app.send_message(target,text); await m.reply('🤫 Whisper sent privately.')
  except: await m.reply('❌ I cannot DM this user. They must start Viora first.')
 @app.on_message(filters.command('whisper'))
 async def whisper(_,m):
  if len(m.command)<3:return await m.reply('/whisper <username|user_id> <text>')
  target=m.command[1]; text=' '.join(m.command[2:]);
  try: uid=int(target) if target.lstrip('-').isdigit() else (await app.get_users(target)).id
  except:return await m.reply('❌ Target not found.')
  await send(uid,f'🤫 <b>Whisper from {m.from_user.first_name}</b>\n{text}',m)
 @app.on_message(filters.regex(r'^@[^\s]+\s+'))
 async def mention_whisper(_,m):
  # Exact @VioraBot <target> <text> form. Username is configurable.
  first,rest=m.text.split(maxsplit=1); botname='@'+c['config'].BOT_USERNAME
  aliases=set(c['config'].WHISPER_ALIASES) | {c['config'].BOT_USERNAME.lower()}
  if first.lstrip('@').lower() not in aliases:return
  parts=rest.split(maxsplit=1)
  if len(parts)<2:return await m.reply(f'Usage: {botname} <username|user_id> <text>')
  target,text=parts
  try: uid=int(target) if target.lstrip('-').isdigit() else (await app.get_users(target)).id
  except:return await m.reply('❌ Target not found.')
  await send(uid,f'🤫 <b>Whisper from {m.from_user.first_name}</b>\n{text}',m)
