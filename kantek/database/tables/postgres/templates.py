from typing import Optional, List

from . import AbstractTableWrapper
from ...types import Template


class Templates(AbstractTableWrapper):
    async def add(self, name: str, content: str, edit: bool) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO templates
                VALUES ($1, $2, $3)
                ON CONFLICT (name) DO UPDATE
                SET content=excluded.content
            """, name, content, edit)

    async def get(self, name: str) -> Optional[Template]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM templates WHERE name = $1', name)
        if row:
            return Template(row['name'], row['content'], row['edit'])
        else:
            return None

    async def get_all(self) -> List[Template]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('SELECT * FROM templates')
        return [Template(row['name'], row['content'], row['edit']) for row in rows]

    async def delete(self, name: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM templates WHERE name = $1", name)
