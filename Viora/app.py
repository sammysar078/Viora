import asyncio
from pyrogram import Client
from Viora import config
from Viora.core.db import DB
from Viora.core.api import API
from Viora.core.game_manager import GameManager
from Viora.services.economy import Economy
from Viora.services.gems import Gems
from Viora.services.powers import Powers
from Viora.services.leaderboard import Leaderboard
from Viora.services.premium import Premium
from Viora.features import start,menu,economy,gems,powers,premium,utilities,interactions,intro,coupons,whisper,group
from Viora.games.engine import reg as games_register
async def main():
 if not config.API_ID or not config.API_HASH or not config.BOT_TOKEN: raise RuntimeError('API_ID, API_HASH and BOT_TOKEN are required.')
 db=DB(config.MONGO_URI,config.MONGO_DB); await db.connect()
 api=API(config.BOT_TOKEN); econ=Economy(db.db); gem=Gems(db.db,econ); prem=Premium(db.db); power=Powers(db.db,gem); leader=Leaderboard(db.db); gm=GameManager(db.db)
 ctx={'db':db.db,'config':config,'api':api,'economy':econ,'gems':gem,'premium':prem,'powers':power,'leader':leader,'games':gm}
 app=Client('Viora',api_id=config.API_ID,api_hash=config.API_HASH,bot_token=config.BOT_TOKEN,workers=8)
 for fn in [start.register,menu.register,economy.register,gems.register,powers.register,premium.register,utilities.register,interactions.register,intro.register,coupons.register,whisper.register,group.register]: await fn(app,ctx)
 games_register(app,ctx)
 @app.on_message()
 async def track(_,m):
  if m.from_user:
   u=await econ.ensure(m.from_user.id,m.from_user.first_name,m.from_user.username)
   name=m.from_user.first_name or ''; username=m.from_user.username or ''
   last=await db.db.name_history.find_one({'user_id':m.from_user.id},sort=[('at',-1)])
   if not last or last.get('name')!=name or last.get('username')!=username:
    await db.db.name_history.insert_one({'user_id':m.from_user.id,'name':name,'username':username,'at':__import__('datetime').datetime.utcnow()})
 await app.start()
 if hasattr(app, 'viora_recover'):
  await app.viora_recover()
 print('Viora started.')
 await asyncio.Event().wait()
if __name__=='__main__': asyncio.run(main())
