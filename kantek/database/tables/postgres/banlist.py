from typing import Dict, Optional, List
from . import AbstractTableWrapper
from ...types import Chat, BlacklistItem, Template, BannedUser

class Banlist(AbstractTableWrapper):
    async def add_user(self, _id: int, reason: str) -> Optional[BannedUser]:
        # unused
        pass

    async def get_user(self, uid: int) -> Optional[BannedUser]:
        """Fetch a users document
        Args:
            uid: User ID
        Returns: None or the Document
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM banlist WHERE id = $1", uid)
        if row:
            return BannedUser(row['id'], row['reason'])

    async def remove(self, uid):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM banlist WHERE id = $1", uid)

    async def get_multiple(self, uids) -> List[BannedUser]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f"SELECT * FROM banlist WHERE id = ANY($1::BIGINT[])", uids)
        return [BannedUser(row['id'], row['reason']) for row in rows]

    async def count_reason(self, reason) -> int:
        async with self.pool.acquire() as conn:
            return (await conn.fetchrow("SELECT count(*) FROM banlist WHERE lower(reason) LIKE lower($1)",
                                        reason))['count']

    async def get_with_reason(self, reason) -> List[BannedUser]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM banlist WHERE lower(reason) LIKE lower($1)", reason)
        return [BannedUser(row['id'], row['reason']) for row in rows]

    async def total_count(self) -> int:
        async with self.pool.acquire() as conn:
            return (await conn.fetchrow("SELECT count(*) FROM banlist"))['count']

    async def upsert_multiple(self, bans) -> None:
        bans = [(int(u['id']), str(u['reason']), datetime.datetime.now(), None) for u in bans]
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    CREATE TEMPORARY TABLE _data
                    (id BIGINT, reason TEXT, date TIMESTAMP, message TEXT)
                    ON COMMIT DROP
                """)
                await conn.copy_records_to_table('_data', records=bans)
                await conn.execute("""
                        INSERT INTO banlist
                        SELECT * FROM _data
                        ON CONFLICT (id)
                        DO UPDATE SET reason=excluded.reason, date=excluded.date
                    """)

    async def get_all(self) -> List[BannedUser]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('SELECT * FROM banlist')
        return [BannedUser(row['id'], row['reason']) for row in rows]

    async def get_all_not_in(self, not_in) -> List[BannedUser]:
        not_in = list(map(int, not_in))
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f"SELECT * FROM banlist WHERE NOT (id = ANY($1::BIGINT[]))", not_in)
        return [BannedUser(row['id'], row['reason']) for row in rows]

