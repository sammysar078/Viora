import asyncio, uuid
from datetime import datetime, timezone

class GameManager:
    def __init__(self, db):
        self.db = db
        self.locks = {}

    def lock(self, gid):
        return self.locks.setdefault(gid, asyncio.Lock())

    async def create(self, chat_id, typ, host, stake, currency='coins', data=None):
        gid = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc)
        doc = {
            'game_id': gid, 'chat_id': chat_id, 'type': typ, 'host_id': host,
            'stake': int(stake), 'currency': currency, 'status': 'joining',
            'created_at': now, 'data': data or {}
        }
        await self.db.games.insert_one(doc)
        await self.db.game_entries.insert_one({'game_id': gid, 'user_id': host,
            'stake': int(stake), 'currency': currency, 'joined_at': now})
        return gid

    async def get(self, gid):
        return await self.db.games.find_one({'game_id': gid})

    async def join(self, gid, uid, stake, currency):
        try:
            await self.db.game_entries.insert_one({'game_id': gid, 'user_id': uid,
                'stake': int(stake), 'currency': currency,
                'joined_at': datetime.now(timezone.utc)})
            return True
        except Exception:
            return False

    async def entries(self, gid):
        return await self.db.game_entries.find({'game_id': gid}).sort('joined_at', 1).to_list(100)

    async def finish(self, gid, data=None):
        return await self.db.games.update_one(
            {'game_id': gid, 'status': 'active'},
            {'$set': {'status': 'finished', 'finished_at': datetime.now(timezone.utc), 'data': data or {}}})

    async def cancel(self, gid):
        return await self.db.games.update_one(
            {'game_id': gid, 'status': {'$in': ['joining', 'active']}},
            {'$set': {'status': 'cancelled', 'finished_at': datetime.now(timezone.utc)}})
