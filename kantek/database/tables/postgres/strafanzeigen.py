
from typing import Dict, Optional, List
from . import AbstractTableWrapper
from ...types import Chat, BlacklistItem, Template, BannedUser

class Strafanzeigen(AbstractTableWrapper):
    async def add(self, data, key):
        async with self.pool.acquire() as conn:
            await conn.execute('INSERT INTO strafanzeigen VALUES ($1, $2)', key, data)
        return key

    async def get(self, key) -> Optional[str]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT data FROM strafanzeigen WHERE key = $1', key)
        if row:
            return row['data']
        else:
            return None

    async def cleanup(self):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM strafanzeigen WHERE creation_date + '30 minutes' < now();")

