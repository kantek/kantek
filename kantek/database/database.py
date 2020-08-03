import secrets
from typing import Union, Dict, List, Optional

from database.types import BlacklistItem, BannedUser, Chat
from utils.config import Config


class UnknownDatabaseError(Exception):
    pass


class DeprecatedDatabaseError(Exception):
    pass


class ItemDoesNotExistError(Exception):
    pass


class Table:
    def __init__(self, parent: 'Database'):
        self.db = parent.db


class Blacklist(Table):
    hex_type = None

    @property
    def bl(self):
        return self.db.blacklists.get(self.hex_type)

    async def add(self, item: str) -> BlacklistItem:
        return await self.bl.add(item)

    async def get_by_value(self, item) -> BlacklistItem:
        return await self.bl.get_by_value(item)

    async def get(self, index) -> BlacklistItem:
        return await self.bl.get(index)

    async def retire(self, item):
        result = await self.bl.retire(item)
        if not result:
            raise ItemDoesNotExistError()

    async def get_all(self) -> List[BlacklistItem]:
        return await self.bl.get_all()

    async def get_indices(self, indices) -> List[BlacklistItem]:
        return await self.bl.get_indices(indices)


class BioBlacklist(Blacklist):
    hex_type = '0x0'


class StringBlacklist(Blacklist):
    hex_type = '0x1'


class ChannelBlacklist(Blacklist):
    hex_type = '0x3'


class DomainBlacklist(Blacklist):
    hex_type = '0x4'


class FileBlacklist(Blacklist):
    hex_type = '0x5'


class MHashBlacklist(Blacklist):
    hex_type = '0x6'


class TLDBlacklist(Blacklist):
    hex_type = '0x7'


class Strafanzeigen(Table):
    async def add(self, content) -> str:
        key = secrets.token_urlsafe(10)
        return await self.db.strafanzeigen.add(content, key)

    async def get(self, sa_key) -> Optional[str]:
        return await self.db.strafanzeigen.get(sa_key)

    async def cleanup(self):
        await self.db.strafanzeigen.cleanup()


class Banlist(Table):
    async def get(self, uid) -> BannedUser:
        return await self.db.banlist.get_user(uid)

    async def add(self, uid: int, reason: str) -> BannedUser:
        return await self.db.banlist.add_user(uid, reason)

    async def remove(self, uid: int) -> None:
        return await self.db.banlist.remove(uid)

    async def get_multiple(self, ids) -> List[BannedUser]:
        return await self.db.banlist.get_multiple(ids)

    async def count_reason(self, reason) -> int:
        return await self.db.banlist.count_reason(reason)

    async def total_count(self) -> int:
        return await self.db.banlist.total_count()

    async def upsert_multiple(self, bans: List[Dict[str, str]]) -> None:
        return await self.db.banlist.upsert_multiple(bans)

    async def get_all(self) -> List[BannedUser]:
        return await self.db.banlist.get_all()

    async def get_all_not_in(self, not_in) -> List[BannedUser]:
        return await self.db.banlist.get_all_not_in(not_in)


class Chats(Table):
    async def add(self, chat_id: int) -> Chat:
        return await self.db.chats.add(chat_id)

    async def get(self, chat_id: int) -> Chat:
        return await self.db.chats.get(chat_id)

    async def lock(self, chat_id: int, permissions: Dict[str, bool]):
        await self.db.chats.lock(chat_id, permissions)

    async def unlock(self, chat_id: int):
        await self.db.chats.unlock(chat_id)

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
        self._map = {
            '0x0': self.bio,
            '0x1': self.string,
            '0x3': self.channel,
            '0x4': self.domain,
            '0x5': self.file,
            '0x6': self.mhash,
        }

    async def get(self, hex_type: str):
        return self._map.get(hex_type)


class Database:
    db: Union['Postgres']

    async def connect(self, config: Config):
        if config.db_type == 'arango':
            raise DeprecatedDatabaseError('ArangoDB has been deprecated. Please use Postgres instead.')
        elif config.db_type == 'postgres':
            from database.postgres import Postgres
            self.db = Postgres()
            await self.db.connect(config.db_host, config.db_port,
                                  config.db_username,
                                  config.db_password,
                                  config.db_name)
        else:
            raise UnknownDatabaseError('Choose from: postgres')
        self.strafanzeigen = Strafanzeigen(self)
        self.banlist = Banlist(self)
        self.blacklists = Blacklists(self)
        self.chats = Chats(self)

    async def disconnect(self):
        await self.db.disconnect()

    async def cleanup(self):
        """This function gets called on every new message and can be used to run cleanup tasks"""
        await self.strafanzeigen.cleanup()
