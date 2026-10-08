from pyrogram import filters
async def register(app,c):
 api=c['api']
 pages={
 'features':('🍀 <b>Viora Features</b>','/bal /pfp /daily /wallet /give /protect /revive /toprich /topkill /economy\n/gems /convert /powers /premium\n/detail /q /voice /font /own /tr /admins /report /owner /id /isdeleted /calc\n/kiss /hug /slap /punch /bite /murder /love /crush /look /brain /stupid_meter /couples\n/truth /dare /puzzle /setintro /intro /whisper'),
 'games':('🎮 <b>Viora Games</b>','/hack /register /guess\n/bluff /enter /drop /judge\n/roulette /join /bid\n/card /bet /flip\n/bomb /pass /rank /leaders /bombcancel /end'),
 'groups':('👥 <b>Groups</b>','/claim — group reward\n/close /open — gaming gate\n/admins /owner /report /help'),
 'promoter':('💸 <b>Promoter</b>','Promoter/referral tools are reserved for the configured Viora campaign. No balance is credited from unverified referrals.'),
 'updates':('📢 <b>Updates</b>','Viora features are organized into independent modules so new games and commands can be added without rewriting the economy.')}
 @app.on_callback_query(filters.regex(r'^menu:'))
 async def menu(_,q):
  key=q.data.split(':',1)[1]; title,body=pages.get(key,pages['features']); kb=api.kb((api.btn('🏠 Home','menu:home',style='primary'),api.btn('⬅️ Back','menu:features',style='danger')))
  if key=='home': return await api.answer(q.id,'Use /start',False)
  await api.edit(q.message.chat.id,q.message.id,title+'\n\n'+body,kb); await api.answer(q.id)
