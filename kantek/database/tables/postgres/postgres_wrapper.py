"""Module containing all operations related to PostgreSQL"""
import datetime
import json
import re

import asyncpg as asyncpg
from asyncpg.pool import Pool
from . import Banlist, Blacklists, Chats, Strafanzeigen, Templates, Bundesnachrichtendienst


class PostgresWrapper:  # pylint: disable = R0902
    wildcard = '%'

    async def connect(self, host, port, username, password, name) -> None:
        if port is None:
            port = 5432
        self.pool: Pool = await asyncpg.create_pool(user=username, password=password,
                                                    database=name, host=host, port=port)

        self.chats: Chats = Chats(self.pool)
        self.blacklists = Blacklists(self.pool)
        self.banlist: Banlist = Banlist(self.pool)
        self.strafanzeigen: Strafanzeigen = Strafanzeigen(self.pool)
        self.templates: Templates = Templates(self.pool)
        self.bundesnachrichtendienst: Bundesnachrichtendienst = Bundesnachrichtendienst(self.pool)

    async def disconnect(self):
        await self.pool.close()

    def convert_wildcard(self, query):
        return re.sub(r'(?<!\\)\*', self.wildcard, query)
