class Leaderboard:
 def __init__(self,db): self.c=db.users
 async def rich(self,n=10): return await self.c.find({}).sort('balance',-1).limit(n).to_list(n)
 async def kills(self,n=10): return await self.c.find({}).sort('kills',-1).limit(n).to_list(n)
 async def rank(self,uid): return await self.c.count_documents({'xp':{'$gt':(await self.c.find_one({'user_id':uid})).get('xp',0)}})+1
