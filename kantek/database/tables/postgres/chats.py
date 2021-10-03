import json
from typing import Dict, Optional

from . import AbstractTableWrapper
from ...types import Chat


class Chats(AbstractTableWrapper):

    async def add(self, chat_id: int) -> Optional[Chat]:
        async with self.pool.acquire() as conn:
            await conn.execute("""
            INSERT INTO chats 
            VALUES ($1, '{}') 
            ON CONFLICT DO NOTHING
            """, chat_id)
        return Chat(chat_id, {})

    async def get(self, chat_id: int) -> Chat:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM chats WHERE id = $1", chat_id)
        if row:
            return Chat(row['id'], json.loads(row['tags']), json.loads(row['permissions'] or '{}'), row['locked'])
        else:
            return await self.add(chat_id)

    async def lock(self, chat_id: int, permissions: Dict[str, bool]) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE chats SET locked = TRUE, permissions=$2 WHERE id = $1",
                               chat_id, json.dumps(permissions))

    async def unlock(self, chat_id: int) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE chats SET locked = FALSE WHERE id = $1", chat_id)

    async def update_tags(self, chat_id: int, new: Dict):
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE chats SET tags=$1 WHERE id=$2", json.dumps(new), chat_id)
