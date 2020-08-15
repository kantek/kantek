"""Module containing all operations related to PostgreSQL"""
import datetime
import json
import re
from typing import Dict, Optional, List

import asyncpg as asyncpg
from asyncpg.pool import Pool

from database.types import BlacklistItem, Chat, BannedUser, Template


class TableWrapper:
    def __init__(self, pool):
        self.pool: Pool = pool


class Chats(TableWrapper):

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


class Blacklist(TableWrapper):
    async def add(self, item: str) -> Optional[BlacklistItem]:
        """Add a Chat to the DB or return an existing one.
        Args:
            item: The id of the chat
        Returns: The chat Document
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(f"INSERT INTO blacklists.{self.name} (item) VALUES ($1) RETURNING id", str(item))
        return BlacklistItem(row['id'], item, False)

    async def get_by_value(self, item: str) -> Optional[BlacklistItem]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(f"SELECT * FROM blacklists.{self.name} WHERE item = $1", str(item))
        if row:
            if row['retired']:
                return None
            else:
                return BlacklistItem(row['id'], row['item'], row['retired'])
        else:
            return None

    async def get(self, index):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(f"SELECT * FROM blacklists.{self.name} WHERE id = $1", index)
        if row:
            return BlacklistItem(row['id'], row['item'], row['retired'])
        else:
            return None

    async def retire(self, item):
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(f"""
                UPDATE blacklists.{self.name} 
                SET retired=TRUE
                WHERE item=$1
                RETURNING id
            """, str(item))
        return result

    async def get_all(self) -> List[BlacklistItem]:
        """Get all strings in the Blacklist."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f"SELECT * FROM blacklists.{self.name} ORDER BY id")
        return [BlacklistItem(row['id'], row['item'], row['retired']) for row in rows]

    async def get_indices(self, indices):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f"SELECT * FROM blacklists.{self.name} WHERE id = any($1::integer[]) ORDER BY id", indices)
        return [BlacklistItem(row['id'], row['item'], row['retired']) for row in rows]


class BioBlacklist(Blacklist):
    """Blacklist with strings in a bio."""
    hex_type = '0x0'
    name = 'bio'


class StringBlacklist(Blacklist):
    """Blacklist with strings in a message"""
    hex_type = '0x1'
    name = 'string'


class ChannelBlacklist(Blacklist):
    """Blacklist with blacklisted channel ids"""
    hex_type = '0x3'
    name = 'channel'


class DomainBlacklist(Blacklist):
    """Blacklist with blacklisted domains"""
    hex_type = '0x4'
    name = 'domain'


class FileBlacklist(Blacklist):
    """Blacklist with blacklisted file sha 512 hashes"""
    hex_type = '0x5'
    name = 'file'


class MHashBlacklist(Blacklist):
    """Blacklist with blacklisted photo hashes"""
    hex_type = '0x6'
    name = 'mhash'


class BanList(TableWrapper):
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


class Strafanzeigen(TableWrapper):
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


class Templates(TableWrapper):
    async def add(self, name: str, content: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO templates
                VALUES ($1, $2)
                ON CONFLICT (name) DO UPDATE
                SET content=excluded.content
            """, name, content)

    async def get(self, name: str) -> Optional[Template]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM templates WHERE name = $1', name)
        if row:
            return Template(row['name'], row['content'])
        else:
            return None

    async def get_all(self) -> List[Template]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('SELECT * FROM templates')
        return [Template(row['name'], row['content']) for row in rows]

    async def delete(self, name: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM templates WHERE name = $1", name)


class Blacklists:
    def __init__(self, pool):
        self.pool = pool
        self.bio = BioBlacklist(pool)
        self.string = StringBlacklist(pool)
        self.channel = ChannelBlacklist(pool)
        self.domain = DomainBlacklist(pool)
        self.file = FileBlacklist(pool)
        self.mhash = MHashBlacklist(pool)
        self._map = {
            '0x0': self.bio,
            '0x1': self.string,
            '0x3': self.channel,
            '0x4': self.domain,
            '0x5': self.file,
            '0x6': self.mhash,
        }

    def get(self, hex_type: str):
        return self._map.get(hex_type)


class Postgres:  # pylint: disable = R0902
    wildcard = '%'

    async def connect(self, host, port, username, password, name) -> None:
        if port is None:
            port = 5432
        self.pool: Pool = await asyncpg.create_pool(user=username, password=password,
                                                    database=name, host=host, port=port)

        self.chats: Chats = Chats(self.pool)
        self.blacklists = Blacklists(self.pool)
        self.banlist: BanList = BanList(self.pool)
        self.strafanzeigen: Strafanzeigen = Strafanzeigen(self.pool)
        self.templates: Templates = Templates(self.pool)

    async def disconnect(self):
        await self.pool.close()

    def convert_wildcard(self, query):
        return re.sub(r'(?<!\\)\*', self.wildcard, query)
