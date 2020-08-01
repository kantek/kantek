import secrets
import time
from typing import Union, Dict, List, Optional

from database.arango import ArangoDB
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

    def add(self, item: str) -> BlacklistItem:
        return getattr(self.db, self.name).add(item)

    def get_by_value(self, item) -> BlacklistItem:
        return getattr(self.db, self.name).get_by_value(item)

    def get(self, index) -> BlacklistItem:
        return getattr(self.db, self.name).get(index)

    def retire(self, item):
        result = getattr(self.db, self.name).retire(item)
        if not result:
            raise ItemDoesNotExistError()

    def get_all(self) -> List[BlacklistItem]:
        return getattr(self.db, self.name).get_all()

    def get_indices(self, indices) -> List[BlacklistItem]:
        return getattr(self.db, self.name).get_indices(indices, self.db)


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
    def add(self, content) -> str:
        key = secrets.token_urlsafe(10)
        creation_date = time.time()
        return self.db.strafanzeigen.add(creation_date, content, key)

    def get(self, sa_key) -> Optional[str]:
        return self.db.strafanzeigen.get(sa_key)


class Banlist(Table):
    def get(self, uid) -> BannedUser:
        return self.db.banlist.get_user(uid)

    def add(self, uid: int, reason: str) -> BannedUser:
        return self.db.banlist.add_user(uid, reason)

    def remove(self, uid: int) -> None:
        return self.db.banlist.remove(uid, self.db)

    def get_multiple(self, ids) -> List[BannedUser]:
        return self.db.banlist.get_multiple(ids, self.db)

    def count_reason(self, reason) -> int:
        return self.db.banlist.count_reason(reason, self.db)

    def total_count(self) -> int:
        return self.db.banlist.total_count(self.db)

    def upsert_multiple(self, bans: List[Dict[str, str]]) -> None:
        return self.db.banlist.upsert_multiple(bans, self.db)

    def get_all(self) -> List[BannedUser]:
        return self.db.banlist.get_all(self.db)

    def get_all_not_in(self, not_in) -> List[BannedUser]:
        return self.db.banlist.get_all_not_in(not_in, self.db)


class Chats(Table):
    def add(self, chat_id: int) -> Chat:
        return self.db.chats.add(chat_id)

    def get(self, chat_id: int) -> Chat:
        return self.db.chats.get(chat_id)

    def update_tags(self, chat_id: int, new: Dict):
        return self.db.chats.update_tags(chat_id, new)


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

    def get(self, hex_type: str):
        return self._map.get(hex_type)


class Database:
    db: Union[ArangoDB]

    def __init__(self, db: str, config: Config):
        if db == 'arango':
            self.db = ArangoDB(config.db_host,
                               config.db_username,
                               config.db_password,
                               config.db_name)
        else:
            raise UnknownDatabaseError('Choose from: arango')
        self.strafanzeigen = Strafanzeigen(self)
        self.banlist = Banlist(self)
        self.blacklists = Blacklists(self)
        self.chats = Chats(self)
