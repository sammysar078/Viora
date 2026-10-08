from datetime import datetime,timezone
MICRO=1000
class Gems:
 def __init__(self,db,econ): self.c=db.users; self.tx=db.gem_transactions; self.e=econ
 async def balance(self,uid):
  u=await self.e.get(uid); return int(u.get('gems',0))
 async def add(self,uid,gems,kind='purchase',ref=None):
  n=int(gems*MICRO); await self.c.update_one({'user_id':uid},{'$inc':{'gems':n}}); await self.tx.insert_one({'user_id':uid,'delta':n,'type':kind,'ref':ref,'at':datetime.now(timezone.utc)})
 async def spend(self,uid,gems,kind='game_bet',ref=None):
  u=await self.e.get(uid); prem=await self.e.premium(u); n=int(gems*MICRO)
  if not prem: return False,'Premium required to use gems.'
  day=u.get('gem_use',{}); key=datetime.now(timezone.utc).date().isoformat(); used=day.get('date')==key and int(day.get('amount',0)) or 0
  if used+n>50*MICRO: return False,'Daily gem usage limit is 50 gems.'
  if day.get('date')==key:
   r=await self.c.update_one({'user_id':uid,'gems':{'$gte':n}},{'$inc':{'gems':-n,'gem_use.amount':n}})
  else:
   r=await self.c.update_one({'user_id':uid,'gems':{'$gte':n}},{'$inc':{'gems':-n},'$set':{'gem_use':{'date':key,'amount':n}}})
  if not r.modified_count: return False,'Not enough gems.'
  await self.tx.insert_one({'user_id':uid,'delta':-n,'type':kind,'ref':ref,'at':datetime.now(timezone.utc)}); return True,''
 async def convert(self,uid,gems):
  ok,msg=await self.spend(uid,gems,'conversion');
  if not ok:return False,msg
  await self.e.add(uid,int(gems)*10000); return True,''
