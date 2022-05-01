from typing import List

from . import AbstractTable
from ..types import Chat, BlacklistItem, Template, BannedUser
from ..errors import ItemDoesNotExistError

class Blacklist(AbstractTable):
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

    async def retire_by_id(self, id):
        result = await self.bl.retire_by_id(id)
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
