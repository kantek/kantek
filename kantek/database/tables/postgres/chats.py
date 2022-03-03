import json
from typing import Dict, Optional

from . import AbstractTableWrapper
from ...types import Chat


class Chats(AbstractTableWrapper):

    async def add(self, chat_id: int, title: Optional[str] = None) -> Optional[Chat]:
        async with self.pool.acquire() as conn:
            await conn.execute("""
            INSERT INTO chats (id, tags, title)
            VALUES ($1, '{}', $2)
            ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title
            WHERE EXCLUDED.title IS NOT NULL
            """, chat_id, title)
        return Chat(id=chat_id, title=title, tags={})

    async def get(self, chat_id: int) -> Chat:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM chats WHERE id = $1", chat_id)
        if row:
            return Chat(
                id=row['id'],
                tags=json.loads(row['tags']),
                title=row['title'],
                permissions=json.loads(row['permissions'] or '{}'),
                locked=row['locked'],
                raid_start=row['raid_start'],
            )

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

    async def start_raid(self, chat_id: int, message_id: int) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE chats SET raid_start = $2 WHERE id = $1", chat_id, message_id)

    async def stop_raid(self, chat_id: int) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE chats SET raid_start = NULL WHERE id = $1", chat_id)
