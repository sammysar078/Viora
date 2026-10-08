from datetime import timedelta
from Viora.config import PREMIUM_DAYS
from Viora.core.common import now
class Premium:
 def __init__(self,db): self.c=db.users
 async def active(self,uid):
  u=await self.c.find_one({'user_id':uid}); return bool(u and u.get('premium_until') and u['premium_until']>now())
 async def grant(self,uid,days=PREMIUM_DAYS):
  u=await self.c.find_one({'user_id':uid}); base=u.get('premium_until') if u and u.get('premium_until') and u['premium_until']>now() else now(); until=base+timedelta(days=days); await self.c.update_one({'user_id':uid},{'$set':{'premium_until':until}},upsert=True); return until
