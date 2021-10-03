from typing import Optional, List

from . import AbstractTableWrapper
from ...types import BNDAction, CharacterClass, BND


class Bundesnachrichtendienst(AbstractTableWrapper):
    async def add(self, chat_id: int, action: BNDAction,
                  pattern: Optional[str] = None, character_class: Optional[CharacterClass] = None) -> BND:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
            INSERT INTO bundesnachrichtendienst (chat_id, action, pattern, character_class)
            VALUES ($1, $2, $3, $4) 
            ON CONFLICT DO NOTHING RETURNING id
            """, chat_id, action, pattern, character_class)
        return BND(row['id'], chat_id, action, pattern, character_class)

    async def get_all_for_chat(self, chat_id: int) -> List[BND]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM bundesnachrichtendienst WHERE chat_id = $1", chat_id)
        if rows:
            return [BND(**row) for row in rows]
        else:
            return []

    async def get(self, uid: int) -> Optional[BND]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM bundesnachrichtendienst WHERE id = $1", uid)
        if row:
            return BND(**row)
        else:
            return None

    async def remove(self, uid: int) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM bundesnachrichtendienst WHERE id = $1", uid)
