import random
from pyrogram import filters
from Viora.core.common import target_from_reply,mention
A={'kiss':'💋 kissed','hug':'🤗 hugged','slap':'👋 slapped','punch':'🥊 punched','bite':'🧛 bit','murder':'💀 murdered','love':'❤️ loves','look':'👀 looked at'}
async def register(app,c):
 @app.on_message(filters.command(list(A)))
 async def act(_,m):
  t=target_from_reply(m); name=mention(t) if t else 'everyone'; cmd=m.command[0].lower(); await m.reply(f"{A[cmd]} {name}!")
 @app.on_message(filters.command('crush'))
 async def crush(_,m):
  t=target_from_reply(m); await m.reply(f'💘 Crush meter for {mention(t) if t else "you"}: {random.randint(0,100)}%')
 @app.on_message(filters.command('brain'))
 async def brain(_,m): await m.reply(f'🧠 Brain power: {random.randint(1,100)}%')
 @app.on_message(filters.command('stupid_meter'))
 async def stupid(_,m): await m.reply(f'🤡 Stupid meter: {random.randint(0,100)}%')
 @app.on_message(filters.command('couples'))
 async def couples(_,m):
  users=[]
  async for x in app.get_chat_members(m.chat.id):
   if not x.user.is_bot:users.append(x.user)
   if len(users)>=20:break
  random.shuffle(users); await m.reply('💞 Couples\n'+'\n'.join(f'{mention(users[i])} ❤️ {mention(users[i+1])}' for i in range(0,len(users)-1,2)) or 'Not enough members.')
 @app.on_message(filters.command('truth'))
 async def truth(_,m): await m.reply(random.choice(['What is your biggest secret?','Who was your first crush?','What is one thing you regret?']))
 @app.on_message(filters.command('dare'))
 async def dare(_,m): await m.reply(random.choice(['Send a funny sticker.','Change your profile bio for 10 minutes.','Compliment the last person who replied.']))
 @app.on_message(filters.command('puzzle'))
 async def puzzle(_,m): await m.reply(random.choice(['What has keys but cannot open locks? A piano.','I speak without a mouth. What am I? An echo.','What gets wetter as it dries? A towel.']))
