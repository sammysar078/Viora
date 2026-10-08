from datetime import timedelta
from random import randint
from Viora.config import *
from Viora.core.common import now,today
class Economy:
 def __init__(self,db): self.c=db.users
 async def ensure(self,uid,name='',username=''):
  await self.c.update_one({'user_id':uid},{'$setOnInsert':{'user_id':uid,'balance':0,'wallet':0,'xp':0,'kills':0,'robs':0,'gems':0,'premium_until':None,'protection_until':None,'gaming_open':True,'daily':{},'kill_day':{},'rob_day':{},'intro':'','emoji':'','powers':{},'stats':{},'dead':False},'$set':{'name':name or 'Unknown','username':username or ''}},upsert=True)
  return await self.get(uid)
 async def get(self,uid): return await self.c.find_one({'user_id':uid})
 async def premium(self,u): return bool(u and u.get('premium_until') and u['premium_until']>now())
 async def add(self,uid,n): await self.c.update_one({'user_id':uid},{'$inc':{'balance':int(n)}})
 async def remove(self,uid,n):
  r=await self.c.update_one({'user_id':uid,'balance':{'$gte':int(n)}},{'$inc':{'balance':-int(n)}}); return r.modified_count==1
 async def transfer(self,a,b,n,tax):
  n=int(n); fee=int(n*tax); recv=n-fee
  if n<=0 or a==b: return False,0
  r=await self.c.update_one({'user_id':a,'balance':{'$gte':n}},{'$inc':{'balance':-n}})
  if not r.modified_count: return False,0
  await self.c.update_one({'user_id':b},{'$inc':{'balance':recv}}); return True,recv
 async def daily_reward(self,uid,prem):
  u=await self.get(uid); d=u.get('daily',{})
  if d.get('date')==today(): return False,0,0
  coins=PREMIUM_DAILY_COINS if prem else NORMAL_DAILY_COINS; xp=PREMIUM_DAILY_XP if prem else NORMAL_DAILY_XP
  await self.c.update_one({'user_id':uid},{'$inc':{'balance':coins,'xp':xp},'$set':{'daily':{'date':today(),'coins':coins}}}); return True,coins,xp
 async def kill(self,uid,prem):
  u=await self.get(uid); d=u.get('kill_day',{}); ramp=u.get('powers',{}).get('rampage',{}).get('until'); lim=(PREMIUM_DAILY_KILLS if prem else NORMAL_DAILY_KILLS)*(2 if ramp and ramp>now() else 1)
  if d.get('date')==today() and d.get('count',0)>=lim: return None
  lo,hi,xlo,xhi=PREMIUM_KILL if prem else NORMAL_KILL; cash=randint(lo,hi); xp=randint(xlo,xhi)
  if d.get('date')==today():
   await self.c.update_one({'user_id':uid},{'$inc':{'balance':cash,'xp':xp,'kills':1,'kill_day.count':1}})
  else:
   await self.c.update_one({'user_id':uid},{'$inc':{'balance':cash,'xp':xp,'kills':1},'$set':{'kill_day':{'date':today(),'count':1}}})
  return cash,xp
 async def rob(self,uid,target_id,prem,requested=None):
  u=await self.get(uid); t=await self.get(target_id); d=u.get('rob_day',{}); ramp=u.get('powers',{}).get('rampage',{}).get('until'); lim=(PREMIUM_DAILY_ROBS if prem else NORMAL_DAILY_ROBS)*(2 if ramp and ramp>now() else 1)
  if d.get('date')==today() and d.get('count',0)>=lim: return 'limit',0
  maxn=(PREMIUM_ROB_MAX if prem else NORMAL_ROB_MAX)*(2 if u.get('powers',{}).get('rampage',{}).get('until') and u['powers']['rampage']['until']>now() else 1); n=min(maxn,int(t.get('balance',0)), int(requested or maxn)); 
  if n<=0: return 'empty',0
  if t.get('protection_until') and t['protection_until']>now(): return 'protected',0
  if t.get('powers',{}).get('cloak',{}).get('until') and t['powers']['cloak']['until']>now(): return 'cloaked',0
  stolen=randint(max(1,n//5),n); xp=randint(0,PREMIUM_ROB_XP_MAX if prem else NORMAL_ROB_XP_MAX)
  deb=await self.c.update_one({'user_id':target_id,'balance':{'$gte':stolen}},{'$inc':{'balance':-stolen}})
  if not deb.modified_count: return 'empty',0
  if d.get('date')==today():
   await self.c.update_one({'user_id':uid},{'$inc':{'balance':stolen,'xp':xp,'robs':1,'rob_day.count':1}})
  else:
   await self.c.update_one({'user_id':uid},{'$inc':{'balance':stolen,'xp':xp,'robs':1},'$set':{'rob_day':{'date':today(),'count':1}}})
  return 'ok',(stolen,xp)
 async def protect(self,uid,prem,days):
  max_days=PREMIUM_PROTECT_DAYS if prem else NORMAL_PROTECT_DAYS
  if days<1 or days>max_days: return False,0
  cost=days*PROTECT_COST_PER_DAY
  if not await self.remove(uid,cost): return False,0
  until=now()+timedelta(days=days); await self.c.update_one({'user_id':uid},{'$set':{'protection_until':until}}); return True,cost
 async def wallet(self,uid,mode,n):
  n=int(n)
  if mode=='deposit':
   r=await self.c.update_one({'user_id':uid,'balance':{'$gte':n}},{'$inc':{'balance':-n,'wallet':n}}); return bool(r.modified_count)
  r=await self.c.update_one({'user_id':uid,'wallet':{'$gte':n}},{'$inc':{'wallet':-n,'balance':n}}); return bool(r.modified_count)
 async def revive(self,uid,target_id=None):
  tid=target_id or uid; u=await self.get(tid)
  if not u or not u.get('dead'): return False
  await self.c.update_one({'user_id':tid},{'$set':{'dead':False}}); return True
