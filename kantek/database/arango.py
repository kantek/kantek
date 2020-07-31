"""Module containing all operations related to ArangoDB"""
from typing import Dict, Optional, Any, List

from pyArango.collection import Collection, Field
from pyArango.connection import Connection
from pyArango.database import Database
from pyArango.document import Document
from pyArango.query import AQLQuery
from pyArango.theExceptions import CreationError, DocumentNotFoundError
from pyArango.validation import Int, NotNull

from database.types import BlacklistItem, Chat, BannedUser


class Chats(Collection):
    """A Collection containing Telegram Chats"""
    _fields = {
        'id': Field([NotNull(), Int()]),
        'tags': Field([NotNull()]),
        'named_tags': Field([NotNull()])
    }

    _validation = {
        'on_save': True,
        'allow_foreign_fields': True
    }

    _properties = {
        "keyOptions": {
            "allowUserKeys": True
        }
    }

    def add(self, chat_id: int) -> Optional[Chat]:
        """Add a Chat to the DB or return an existing one.
        Args:
            chat_id: The id of the chat
        Returns: The chat Document
        """
        data = {'_key': str(chat_id),
                'id': chat_id,
                'tags': [],
                'named_tags': {}}
        try:
            doc = self.createDocument(data)
            doc.save()
            return Chat(chat_id, {})
        except CreationError:
            return None

    def get(self, chat_id: int) -> Chat:
        """Return a Chat document
        Args:
            chat_id: The id of the chat
        Returns: The chat Document
        """
        try:
            doc = self[chat_id]
            return Chat(doc['id'], doc['named_tags'].getStore())
        except DocumentNotFoundError:
            return self.add(chat_id)

    def update_tags(self, chat_id: int, new: Dict):
        _document = self[chat_id]
        _document['named_tags'] = new
        _document.save()


class AutobahnBlacklist(Collection):
    """Base class for all types of Blacklists."""
    _fields = {
        'string': Field([NotNull()]),
    }

    _validation = {
        'on_save': True,
    }

    _properties = {
        'keyOptions': {
            'allowUserKeys': False,
            'type': 'autoincrement',
            'offset': '1'
        }
    }

    def add(self, item: str) -> Optional[BlacklistItem]:
        """Add a Chat to the DB or return an existing one.
        Args:
            item: The id of the chat
        Returns: The chat Document
        """
        data = {'string': item}

        try:
            doc = self.createDocument(data)
            doc.save()
            return BlacklistItem(doc["_key"], doc['string'], False)
        except CreationError:
            return None

    def get_by_value(self, item: str) -> Optional[BlacklistItem]:
        doc = self.fetchByExample({'string': item}, batchSize=1)
        if doc:
            doc = doc[0]
            return BlacklistItem(doc["_key"], doc['string'], False)
        else:
            return None

    def get(self, index):
        doc = self.fetchDocument(index).getStore()
        return BlacklistItem(doc["_key"], doc['string'], False)

    def retire(self, item):
        existing_one: Document = self.fetchFirstExample({'string': item})
        if existing_one:
            existing_one[0].delete()
        else:
            return False

    def get_all(self) -> List[BlacklistItem]:
        """Get all strings in the Blacklist."""
        return [BlacklistItem(doc["_key"], doc['string'], False)
                for doc in self.fetchAll()]

    def get_indices(self, indices, db):
        documents = db.query('FOR doc IN @@blacklist '
                             'FILTER doc._key in @keys '
                             'RETURN doc',
                             bind_vars={'@blacklist': self.name,
                                        'keys': map(str, indices)})
        return [BlacklistItem(doc["_key"], doc['string'], False)
                for doc in documents]


class AutobahnBioBlacklist(AutobahnBlacklist):
    """Blacklist with strings in a bio."""
    hex_type = '0x0'


class AutobahnStringBlacklist(AutobahnBlacklist):
    """Blacklist with strings in a message"""
    hex_type = '0x1'


class AutobahnFilenameBlacklist(AutobahnBlacklist):
    """Blacklist with strings in a Filename"""
    hex_type = '0x2'


class AutobahnChannelBlacklist(AutobahnBlacklist):
    """Blacklist with blacklisted channel ids"""
    hex_type = '0x3'


class AutobahnDomainBlacklist(AutobahnBlacklist):
    """Blacklist with blacklisted domains"""
    hex_type = '0x4'


class AutobahnFileBlacklist(AutobahnBlacklist):
    """Blacklist with blacklisted file sha 512 hashes"""
    hex_type = '0x5'


class AutobahnMHashBlacklist(AutobahnBlacklist):
    """Blacklist with blacklisted photo hashes"""
    hex_type = '0x6'


class AutobahnTLDBlacklist(AutobahnBlacklist):
    """Blacklist with blacklisted top level domains"""
    hex_type = '0x7'


class BanList(Collection):
    """A list of banned ids and their reason"""
    _fields = {
        'id': Field([NotNull()]),
        'ban_reason': Field([NotNull()])
    }

    _validation = {
        'on_save': True,
    }

    _properties = {
        'keyOptions': {
            'allowUserKeys': True,
        }
    }

    def add_user(self, _id: int, reason: str) -> Optional[BannedUser]:
        """Add a Chat to the DB or return an existing one.
        Args:
            _id: The id of the User
            reason: The ban reason
        Returns: The chat Document
        """
        data = {
            '_key': _id,
            'id': _id,
            'reason': reason
        }

        try:
            doc = self.createDocument(data)
            doc.save()
            return BannedUser(doc['id'], doc['reason'])
        except CreationError:
            return None

    def get_user(self, uid: int) -> Optional[BannedUser]:
        """Fetch a users document
        Args:
            uid: User ID
        Returns: None or the Document
        """
        try:
            doc = self.fetchDocument(uid)
            return BannedUser(doc['id'], doc['reason'])
        except DocumentNotFoundError:
            return None

    def remove(self, uid, db):
        db.query('REMOVE {"_key": @uid} IN BanList', bind_vars={'uid': str(uid)})

    def get_multiple(self, uids, db) -> List[BannedUser]:
        docs = db.query('For doc in BanList '
                        'FILTER doc._key in @ids '
                        'RETURN doc', bind_vars={'ids': map(str, uids)})
        return [BannedUser(doc['id'], doc['reason']) for doc in docs]

    def count_reason(self, reason, db) -> int:
        return db.query(
            'FOR doc IN BanList '
            'FILTER doc.reason LIKE @reason '
            'COLLECT WITH COUNT INTO length '
            'RETURN length', bind_vars={'reason': reason}).result[0]

    def total_count(self, db) -> int:
        return db.query('FOR doc IN BanList '
                        'COLLECT WITH COUNT INTO length '
                        'RETURN length').result[0]

    def upsert_multiple(self, bans, db) -> None:
        bans = [{"_key": ban['id'], **ban} for ban in bans]
        db.query('FOR ban in @banlist '
                 'UPSERT {"_key": ban.id, "id": ban.id} '
                 'INSERT ban '
                 'UPDATE {"reason": ban.reason} '
                 'IN BanList', bind_vars={'banlist': bans})

    def get_all(self, db) -> List[BannedUser]:
        docs = db.query('For doc in BanList RETURN doc')
        return [BannedUser(doc['id'], doc['reason']) for doc in docs]

    def get_all_not_in(self, not_in, db) -> List[BannedUser]:
        docs = db.query('For doc in BanList '
                        'FILTER doc._key not in @ids '
                        'RETURN doc', bind_vars={'ids': not_in})

        return [BannedUser(doc['id'], doc['reason']) for doc in docs]


class Strafanzeigen(Collection):
    """A Collection containing Telegram Chats"""
    _fields = {
        'creation_date': Field([NotNull()]),
        'data': Field([NotNull()]),
        'key': Field([NotNull()])
    }

    _validation = {
        'on_save': True,
    }

    def add(self, creation_date, content, key):
        data = {
            'creation_date': creation_date,
            'data': content,
            'key': key
        }

        try:
            doc = self.createDocument(data)
            doc.save()
            return key
        except CreationError:
            return None

    def get(self, key) -> Optional[str]:
        try:
            return self.fetchByExample({'key': key}, 1)[0]['data']
        except IndexError:
            return None


class ArangoDB:  # pylint: disable = R0902
    """Handle creation of all required Documents."""

    def __init__(self, host, username, password, name) -> None:
        self.conn = Connection(arangoURL=host,
                               username=username,
                               password=password)
        self.db = self._get_db(name)
        self.chats: Chats = self._get_collection('Chats')
        self.ab_bio_blacklist: AutobahnBioBlacklist = self._get_collection('AutobahnBioBlacklist')
        self.ab_string_blacklist: AutobahnStringBlacklist = self._get_collection(
            'AutobahnStringBlacklist')
        self.ab_channel_blacklist: AutobahnChannelBlacklist = self._get_collection(
            'AutobahnChannelBlacklist')
        self.ab_domain_blacklist: AutobahnDomainBlacklist = self._get_collection(
            'AutobahnDomainBlacklist')
        self.ab_file_blacklist: AutobahnFileBlacklist = self._get_collection(
            'AutobahnFileBlacklist')
        self.ab_mhash_blacklist: AutobahnMHashBlacklist = self._get_collection(
            'AutobahnMHashBlacklist')
        self.ab_tld_blacklist: AutobahnTLDBlacklist = self._get_collection(
            'AutobahnTLDBlacklist')
        self.ab_collection_map = {
            '0x0': self.ab_bio_blacklist,
            '0x1': self.ab_string_blacklist,
            '0x3': self.ab_channel_blacklist,
            '0x4': self.ab_domain_blacklist,
            '0x5': self.ab_file_blacklist,
            '0x6': self.ab_mhash_blacklist,
            '0x7': self.ab_tld_blacklist
        }
        self.banlist: BanList = self._get_collection('BanList')
        self.strafanzeigen: Strafanzeigen = self._get_collection('Strafanzeigen')
        self.strafanzeigen.ensureTTLIndex(['creation_date'], 30 * 60)

    def query(self, query: str, batch_size: int = 100, raw_results: bool = False,
              bind_vars: Dict = None, options: Dict = None,
              count: bool = False, full_count: bool = False,
              json_encoder: bool = None, **kwargs: Any) -> AQLQuery:  # pylint: disable = R0913
        """Wrapper around the pyArango AQLQuery to avoid having to do `db.db.AQLQuery`."""
        bind_vars = bind_vars or {}
        options = options or {}
        return self.db.AQLQuery(query, rawResults=raw_results, batchSize=batch_size,
                                bindVars=bind_vars, options=options, count=count,
                                fullCount=full_count,
                                json_encoder=json_encoder, **kwargs)

    def _get_db(self, db: str) -> Database:
        """Return a database. Create it if it doesn't exist yet.
        Args:
            db: The name of the Database
        Returns: The Database object
        """
        if self.conn.hasDatabase(db):
            return self.conn[db]
        else:
            return self.conn.createDatabase(db)

    def _get_collection(self, collection: str) -> Collection:
        """Return a collection of create it if it doesn't exist yet.
        Args:
            collection: The name of the collection
        Returns: The Collection object
        """
        if self.db.hasCollection(collection):
            return self.db[collection]
        else:
            return self.db.createCollection(collection, replication_factor=1)
