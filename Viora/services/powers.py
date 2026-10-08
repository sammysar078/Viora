from datetime import timedelta
from Viora.config import POWER_COSTS,POWER_EFFECTS
from Viora.core.common import now
class Powers:
 def __init__(self,db,gems): self.c=db.users; self.g=gems
 async def definitions(self): return POWER_COSTS
 async def activate(self,uid,name,days):
  name=name.lower().strip();
  if name not in POWER_COSTS: return False,'Unknown power.'
  days=max(1,min(int(days),30)); ok,msg=await self.g.spend(uid,POWER_COSTS[name]*days,'power',name)
  if not ok:return False,msg
  u=await self.c.find_one({'user_id':uid}); p=u.get('powers',{}); old=p.get(name,{}).get('until'); until=now()+timedelta(days=days) if not old or old<now() else old+timedelta(days=days)
  await self.c.update_one({'user_id':uid},{'$set':{f'powers.{name}':{'until':until,'activated':now(),'days':days}}}); return True,until
 async def active(self,uid):
  u=await self.c.find_one({'user_id':uid}); p=u.get('powers',{}); return {k:v for k,v in p.items() if v.get('until') and v['until']>now()}
