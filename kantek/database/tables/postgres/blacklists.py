from typing import Dict, Optional, List
from . import AbstractTableWrapper
from ...types import Chat, BlacklistItem, Template, BannedUser
class Blacklist(AbstractTableWrapper):
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

    async def retire_by_id(self, id):
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(f"""
                UPDATE blacklists.{self.name}
                SET retired=TRUE
                WHERE id=$1
                RETURNING id
            """, str(id))
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
