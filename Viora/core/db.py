from motor.motor_asyncio import AsyncIOMotorClient
class DB:
    def __init__(self,uri,name): self.uri=uri; self.name=name; self.client=None; self.db=None
    async def connect(self):
        self.client=AsyncIOMotorClient(self.uri,serverSelectionTimeoutMS=5000); await self.client.admin.command('ping'); self.db=self.client[self.name]
        await self.db.users.create_index('user_id',unique=True); await self.db.groups.create_index('chat_id',unique=True)
        await self.db.group_claims.create_index([('chat_id',1),('user_id',1)],unique=True); await self.db.coupons.create_index([('chat_id',1),('code',1)],unique=True)
        await self.db.coupon_claims.create_index([('chat_id',1),('code',1),('user_id',1)],unique=True)
        await self.db.games.create_index([('chat_id',1),('type',1),('status',1)]); await self.db.game_entries.create_index([('game_id',1),('user_id',1)],unique=True)
        await self.db.reports.create_index([('chat_id',1),('created_at',-1)])
        await self.db.payments.create_index('charge_id',unique=True); await self.db.name_history.create_index([('user_id',1),('at',-1)])
        return self.db
    async def close(self):
        if self.client: self.client.close()
