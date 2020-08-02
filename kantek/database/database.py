import secrets
import time
from typing import Union, Dict, List, Optional

from database.arango import ArangoDB
from database.postgres import Postgres
from database.types import BlacklistItem, BannedUser, Chat
from utils.config import Config


class UnknownDatabaseError(Exception):
    pass


class ItemDoesNotExistError(Exception):
    pass


class Table:
    def __init__(self, parent: 'Database'):
        self.db = parent.db


class Blacklist(Table):
    # temporary until I remove arangodb
    name = None

    async def add(self, item: str) -> BlacklistItem:
        return await getattr(self.db, self.name).add(item)

    async def get_by_value(self, item) -> BlacklistItem:
        return await getattr(self.db, self.name).get_by_value(item)

    async def get(self, index) -> BlacklistItem:
        return await getattr(self.db, self.name).get(index)

    async def retire(self, item):
        result = await getattr(self.db, self.name).retire(item)
        if not result:
            raise ItemDoesNotExistError()

    async def get_all(self) -> List[BlacklistItem]:
        return await getattr(self.db, self.name).get_all()

    async def get_indices(self, indices) -> List[BlacklistItem]:
        return await getattr(self.db, self.name).get_indices(indices, self.db)


class BioBlacklist(Blacklist):
    """Blacklist with strings in a bio."""
    hex_type = '0x0'
    name = 'ab_bio_blacklist'


class StringBlacklist(Blacklist):
    """Blacklist with strings in a message"""
    hex_type = '0x1'
    name = 'ab_string_blacklist'


class ChannelBlacklist(Blacklist):
    """Blacklist with blacklisted channel ids"""
    hex_type = '0x3'
    name = 'ab_channel_blacklist'


class DomainBlacklist(Blacklist):
    """Blacklist with blacklisted domains"""
    hex_type = '0x4'
    name = 'ab_domain_blacklist'


class FileBlacklist(Blacklist):
    """Blacklist with blacklisted file sha 512 hashes"""
    hex_type = '0x5'
    name = 'ab_file_blacklist'


class MHashBlacklist(Blacklist):
    """Blacklist with blacklisted photo hashes"""
    hex_type = '0x6'
    name = 'ab_mhash_blacklist'


class TLDBlacklist(Blacklist):
    """Blacklist with blacklisted top level domains"""
    hex_type = '0x7'
    name = 'ab_tld_blacklist'


class Strafanzeigen(Table):
    async def add(self, content) -> str:
        key = secrets.token_urlsafe(10)
        return await self.db.strafanzeigen.add(content, key)

    async def get(self, sa_key) -> Optional[str]:
        return await self.db.strafanzeigen.get(sa_key)


class Banlist(Table):
    async def get(self, uid) -> BannedUser:
        return await self.db.banlist.get_user(uid)

    async def add(self, uid: int, reason: str) -> BannedUser:
        return await self.db.banlist.add_user(uid, reason)

    async def remove(self, uid: int) -> None:
        return await self.db.banlist.remove(uid, self.db)

    async def get_multiple(self, ids) -> List[BannedUser]:
        return await self.db.banlist.get_multiple(ids, self.db)

    async def count_reason(self, reason) -> int:
        return await self.db.banlist.count_reason(reason, self.db)

    async def total_count(self) -> int:
        return await self.db.banlist.total_count(self.db)

    async def upsert_multiple(self, bans: List[Dict[str, str]]) -> None:
        return await self.db.banlist.upsert_multiple(bans, self.db)

    async def get_all(self) -> List[BannedUser]:
        return await self.db.banlist.get_all(self.db)

    async def get_all_not_in(self, not_in) -> List[BannedUser]:
        return await self.db.banlist.get_all_not_in(not_in, self.db)


class Chats(Table):
    async def add(self, chat_id: int) -> Chat:
        return await self.db.chats.add(chat_id)

    async def get(self, chat_id: int) -> Chat:
        return await self.db.chats.get(chat_id)

    async def update_tags(self, chat_id: int, new: Dict):
        return await self.db.chats.update_tags(chat_id, new)


class Blacklists:
    def __init__(self, parent: 'Database'):
        self.db = parent.db
        self.bio = BioBlacklist(parent)
        self.string = StringBlacklist(parent)
        self.channel = ChannelBlacklist(parent)
        self.domain = DomainBlacklist(parent)
        self.file = FileBlacklist(parent)
        self.mhash = MHashBlacklist(parent)
        self.tld = TLDBlacklist(parent)
        self._map = {
            '0x0': self.bio,
            '0x1': self.string,
            '0x3': self.channel,
            '0x4': self.domain,
            '0x5': self.file,
            '0x6': self.mhash,
            '0x7': self.tld
        }

    async def get(self, hex_type: str):
        return self._map.get(hex_type)


class Database:
    db: Union[ArangoDB, Postgres]

    async def connect(self, config: Config):
        if config.db_type == 'arango':
            self.db = ArangoDB()
            await self.db.connect(config.db_host, config.db_port,
                                  config.db_username,
                                  config.db_password,
                                  config.db_name)
        elif config.db_type == 'postgres':
            self.db = Postgres()
            await self.db.connect(config.db_host, config.db_port,
                                  config.db_username,
                                  config.db_password,
                                  config.db_name)
        else:
            raise UnknownDatabaseError('Choose from: arango')
        self.strafanzeigen = Strafanzeigen(self)
        self.banlist = Banlist(self)
        self.blacklists = Blacklists(self)
        self.chats = Chats(self)
