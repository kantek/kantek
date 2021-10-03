from typing import Union

from .tables import Banlist, Blacklists, Chats, Strafanzeigen, Templates
from .tables.bundesnachrichtendienst import Bundesnachrichtendienst
from .. import Config
from .errors import DeprecatedDatabaseError, UnknownDatabaseError


class Database:
    db: Union['PostgresWrapper']

    async def connect(self, config: Config):
        if config.db_type == 'arango':
            raise DeprecatedDatabaseError('ArangoDB has been deprecated. Please use Postgres instead.')
        elif config.db_type == 'postgres':
            from .tables.postgres import PostgresWrapper
            self.db = PostgresWrapper()
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
        self.templates = Templates(self)
        self.bundesnachrichtendienst = Bundesnachrichtendienst(self)

    async def disconnect(self):
        await self.db.disconnect()

    async def cleanup(self):
        """This function gets called on every new message and can be used to run cleanup tasks"""
        await self.strafanzeigen.cleanup()
