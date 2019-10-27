"""Module containing all operations related to MySQL"""
import json
from typing import Dict

import pymysql
import pymysql.connections
import pymysql.cursors

import config


class Chats:
    """A table containing Telegram Chats"""
    name = 'chats'

    def __init__(self, db: pymysql.connections.Connection) -> None:
        self.db = db

        with self.db.cursor() as cursor:
            cursor.execute('''create table if not exists `{}` (
                `id` varchar(255) not null primary key,
                `tags` text not null,
                `named_tags` text not null
            )'''.format(self.name))

        self.db.commit()

    def add_chat(self, chat_id: int) -> Dict:
        """Add a Chat to the DB or return an existing one.

        Args:
            chat_id: The id of the chat

        Returns: The chat Document

        """
        with self.db.cursor() as cursor:
            sql = 'insert ignore into `{}` (`id`, `tags`, `named_tags`) values (%s, "[]", "{{}}")'.format(
                self.name)
            cursor.execute(sql, (chat_id,))

        self.db.commit()

        with self.db.cursor() as cursor:
            sql = 'select * from `{}` where `id` = %s'.format(self.name)
            cursor.execute(sql, (chat_id,))

            chat = cursor.fetchone()
            chat['tags'] = json.loads(chat['tags'])
            chat['named_tags'] = json.loads(chat['named_tags'])
            return chat

    def get_chat(self, chat_id: int) -> Dict:
        """Return a Chat document

        Args:
            chat_id: The id of the chat

        Returns: The chat Document

        """
        with self.db.cursor() as cursor:
            sql = 'select * from `{}` where `id` = %s'.format(self.name)
            cursor.execute(sql, (str(chat_id),))
            chat = cursor.fetchone()

        if chat is None:
            return self.add_chat(chat_id)
        else:
            chat['tags'] = json.loads(chat['tags'])
            chat['named_tags'] = json.loads(chat['named_tags'])
            return chat


class AutobahnBlacklist:
    """Base class for all types of Blacklists."""
    name = None

    def __init__(self, db: pymysql.connections.Connection) -> None:
        self.db = db

        with self.db.cursor() as cursor:
            cursor.execute('''create table if not exists `{}` (
                `id` int not null auto_increment primary key,
                `string` varchar(255) not null unique
            )'''.format(self.name))

        self.db.commit()

    def add_string(self, string: str) -> Dict:
        """Add a Chat to the DB or return an existing one.

        Args:
            string: The id of the chat

        Returns: The Document

        """
        with self.db.cursor() as cursor:
            sql = 'insert ignore into `{}` (`string`) values (%s)'.format(self.name)
            cursor.execute(sql, (string,))

        self.db.commit()

        with self.db.cursor() as cursor:
            sql = 'select * from `{}` where `string` = %s'.format(self.name)
            cursor.execute(sql, (string,))
            return cursor.fetchone()

    def delete_string(self, string: str) -> None:
        """Delete a Chat from the DB.

        Args:
            string: The id of the chat

        Returns: None

        """
        with self.db.cursor() as cursor:
            sql = 'delete from `{}` where `string` = %s'.format(self.name)
            cursor.execute(sql, (string,))

        self.db.commit()

    def get_string(self, string: str) -> Dict:
        """Get a Chat from the DB or return an existing one.

        Args:
            string: The id of the chat

        Returns: The Document

        """
        with self.db.cursor() as cursor:
            sql = 'select * from `{}` where `string` = %s'.format(self.name)
            cursor.execute(sql, (string,))
            return cursor.fetchone()

    def get_all(self) -> Dict:
        """Get all strings in the Blacklist."""
        with self.db.cursor() as cursor:
            sql = 'select * from `{}`'.format(self.name)
            cursor.execute(sql)
            return {doc['string']: doc['id'] for doc in cursor.fetchall()}


class AutobahnBioBlacklist(AutobahnBlacklist):
    """Blacklist with strings in a bio."""
    name = 'bio_blacklist'
    hex_type = '0x0'


class AutobahnStringBlacklist(AutobahnBlacklist):
    """Blacklist with strings in a message"""
    name = 'string_blacklist'
    hex_type = '0x1'


class AutobahnFilenameBlacklist(AutobahnBlacklist):
    """Blacklist with strings in a Filename"""
    name = 'filename_blacklist'
    hex_type = '0x2'


class AutobahnChannelBlacklist(AutobahnBlacklist):
    """Blacklist with blacklisted channel ids"""
    name = 'channel_blacklist'
    hex_type = '0x3'


class AutobahnDomainBlacklist(AutobahnBlacklist):
    """Blacklist with blacklisted domains"""
    name = 'domain_blacklist'
    hex_type = '0x4'


class AutobahnFileBlacklist(AutobahnBlacklist):
    """Blacklist with blacklisted domains"""
    name = 'file_blacklist'
    hex_type = '0x5'


class AutobahnMHashBlacklist(AutobahnBlacklist):
    """Blacklist with blacklisted domains"""
    name = 'mhash_blacklist'
    hex_type = '0x6'


class BanList:
    """A list of banned ids and their reason"""
    name = 'banlist'

    def __init__(self, db: pymysql.connections.Connection):
        self.db = db

        with self.db.cursor() as cursor:
            cursor.execute('''create table if not exists `{}` (
                `id` int not null primary key,
                `ban_reason` varchar(255) not null
            )'''.format(self.name))

        self.db.commit()

    def add_user(self, _id: int, reason: str) -> Dict:
        """Add a Chat to the DB or return an existing one.

        Args:
            _id: The id of the User
            reason: The ban reason

        Returns: The chat Document

        """
        with self.db.cursor() as cursor:
            sql = 'insert ignore into `{}` (`id`, `string`) values (%s, %s)'.format(self.name)
            cursor.execute(sql, (_id, reason))

        self.db.commit()

        with self.db.cursor() as cursor:
            sql = 'select * from `{}` where `id` = %s'.format(self.name)
            cursor.execute(sql, (_id,))
            return cursor.fetchone()


class MySQLDB:
    """Handle creation of all required Documents."""

    def __init__(self):
        self._db = pymysql.connect(host=config.db_host, user=config.db_username,
                                   password=config.db_password, db=config.db_name,
                                   cursorclass=pymysql.cursors.DictCursor)
        self.groups = self._get_table(Chats)
        self.ab_bio_blacklist = self._get_table(AutobahnBioBlacklist)
        self.ab_string_blacklist = self._get_table(AutobahnStringBlacklist)
        self.ab_filename_blacklist = self._get_table(AutobahnFilenameBlacklist)
        self.ab_channel_blacklist = self._get_table(AutobahnChannelBlacklist)
        self.ab_domain_blacklist = self._get_table(AutobahnDomainBlacklist)
        self.ab_file_blacklist = self._get_table(AutobahnFileBlacklist)
        self.ab_mhash_blacklist = self._get_table(AutobahnMHashBlacklist)
        self.ab_collection_map = {
            '0x0': self.ab_bio_blacklist,
            '0x1': self.ab_string_blacklist,
            '0x2': self.ab_filename_blacklist,
            '0x3': self.ab_channel_blacklist,
            '0x4': self.ab_domain_blacklist,
            '0x5': self.ab_file_blacklist,
            '0x6': self.ab_mhash_blacklist
        }
        self.banlist = self._get_table(BanList)

    @property
    def cursor(self):
        """Wrapper around the PyMySQL Connection.cursor to avoid having to do `db.db.cursor`."""
        self._db.ping(reconnect=True)
        return self._db.cursor

    def commit(self):
        """Wrapper around the PyMySQL Connection.commit to avoid having to do `db.db.commit`."""
        return self._db.commit()

    def _get_table(self, table):
        """Return a table or create it if it doesn't exist yet.

        Args:
            table: The name of the table

        Returns: The Table object

        """
        return table(self)
