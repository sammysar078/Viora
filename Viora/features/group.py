from pyrogram import filters
from Viora.config import CLAIM_REWARD,OWNER_IDS
async def register(app,c):
 e=c['economy']; db=c['db']
 @app.on_message(filters.command('claim') & filters.group)
 async def claim(_,m):
  if not m.from_user:return
  await e.ensure(m.from_user.id,m.from_user.first_name,m.from_user.username)
  try: await db.group_claims.insert_one({'chat_id':m.chat.id,'user_id':m.from_user.id})
  except Exception:return await m.reply('🎁 You already claimed your reward in this group.')
  await e.add(m.from_user.id,CLAIM_REWARD); await m.reply(f'🎁 Claimed {CLAIM_REWARD:,} coins!')
 @app.on_message(filters.command('help'))
 async def help_(_,m): await m.reply('📚 <b>Viora Help</b>\n\n💰 Economy: /bal /pfp /daily /rob /kill /revive /give /wallet /protect /check /toprich /topkill /economy\n💎 Premium/Gems: /pay /setemoji /gems /buygems /convert /powers /pinfo /act /mypowers /ph\n🎮 Games: /hack /register /guess /bluff /enter /drop /judge /roulette /join /bid /card /bet /flip /bomb /pass /rank /leaders /end /bombcancel\n🎟 Coupons: /create_coupon /coupon /del_coupon /status /coupons\n👥 Groups: /claim /close /open /admins /report /owner\n🛠 Utilities: /id /detail /calc /c /tr /voice /font /q /own /isdeleted\n💞 Fun: /kiss /hug /slap /punch /bite /murder /love /crush /look /brain /stupid_meter /couples /truth /dare /puzzle /setintro /intro /whisper')

 @app.on_message(filters.command('close') & filters.group)
 async def close(_,m):
  try:
   member=await app.get_chat_member(m.chat.id,m.from_user.id)
   if not (member.privileges and member.privileges.can_manage_chat): return await m.reply('❌ Group admin only.')
  except Exception: return await m.reply('❌ Could not verify admin rights.')
  await db.groups.update_one({'chat_id':m.chat.id},{'$set':{'gaming_open':False}},upsert=True)
  await m.reply('🔒 Viora gaming commands are now closed in this group. Use /open to reopen them.')
 @app.on_message(filters.command('open') & filters.group)
 async def open_( _,m):
  try:
   member=await app.get_chat_member(m.chat.id,m.from_user.id)
   if not (member.privileges and member.privileges.can_manage_chat): return await m.reply('❌ Group admin only.')
  except Exception: return await m.reply('❌ Could not verify admin rights.')
  await db.groups.update_one({'chat_id':m.chat.id},{'$set':{'gaming_open':True}},upsert=True)
  await m.reply('🔓 Viora gaming commands are now open in this group.')

 @app.on_message(filters.command('id'))
 async def ident(_,m): await m.reply(f'🆔 User ID: <code>{m.from_user.id}</code>\nChat ID: <code>{m.chat.id}</code>')
