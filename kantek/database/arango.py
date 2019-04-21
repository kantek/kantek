"""Module containing all operations related to ArangoDB"""
from typing import Optional

from pyArango.collection import Collection, Field
from pyArango.connection import Connection
from pyArango.database import Database
from pyArango.document import Document
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


# class Group(Document):


class ArangoDB:
    """Handle creation of all required Documents."""
    def __init__(self) -> None:
        self.conn = Connection(arangoURL=config.db_host,
                               username=config.db_username,
                               password=config.db_password)
        self.db = self._get_db(config.db_name)
        self.groups: Chats = self._get_collection('Chats')

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
