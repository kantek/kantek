"""Module containing all operations related to ArangoDB"""
from typing import Dict, Optional, Any

from pyArango.collection import Collection, Field
from pyArango.connection import Connection
from pyArango.database import Database
from pyArango.document import Document
from pyArango.query import AQLQuery
from pyArango.theExceptions import CreationError, DocumentNotFoundError
from pyArango.validation import Int, NotNull

import config


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

    def add_chat(self, chat_id: int) -> Optional[Document]:
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
            return doc
        except CreationError:
            return None

    def get_chat(self, chat_id: int) -> Document:
        """Return a Chat document

        Args:
            chat_id: The id of the chat

        Returns: The chat Document

        """
        try:
            return self[chat_id]
        except DocumentNotFoundError:
            return self.add_chat(chat_id)


class AutobahnBlacklist(Collection):
    """Base class for all types of Blacklists."""
    _fields = {
        'strings': Field([NotNull()]),
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

    def add_string(self, string: str) -> Optional[Document]:
        """Add a Chat to the DB or return an existing one.

        Args:
            str: The id of the chat

        Returns: The chat Document

        """
        data = {'string': string}

        try:
            doc = self.createDocument(data)
            doc.save()
            return doc
        except CreationError:
            return None


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

    def add_user(self, _id: int, reason: str) -> Optional[Document]:
        """Add a Chat to the DB or return an existing one.

        Args:
            _id: The id of the User
            reason: The ban reason

        Returns: The chat Document

        """
        data = {'_key': _id,
                'id': _id,
                'reason': reason}

        try:
            doc = self.createDocument(data)
            doc.save()
            return doc
        except CreationError:
            return None


class ArangoDB:  # pylint: disable = R0902
    """Handle creation of all required Documents."""

    def __init__(self) -> None:
        self.conn = Connection(arangoURL=config.db_host,
                               username=config.db_username,
                               password=config.db_password)
        self.db = self._get_db(config.db_name)
        self.groups: Chats = self._get_collection('Chats')
        self.ab_bio_blacklist: AutobahnBioBlacklist = self._get_collection('AutobahnBioBlacklist')
        self.ab_string_blacklist: AutobahnStringBlacklist = self._get_collection(
            'AutobahnStringBlacklist')
        self.ab_filename_blacklist: AutobahnFilenameBlacklist = self._get_collection(
            'AutobahnFilenameBlacklist')
        self.ab_channel_blacklist: AutobahnChannelBlacklist = self._get_collection(
            'AutobahnChannelBlacklist')
        self.ab_collection_map = {
            '0x0': self.ab_bio_blacklist,
            '0x1': self.ab_string_blacklist,
            '0x2': self.ab_filename_blacklist,
            '0x3': self.ab_channel_blacklist
        }
        self.banlist: BanList = self._get_collection('BanList')

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
            return self.db.createCollection(collection)
