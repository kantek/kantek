from typing import List, Dict

from . import AbstractTable
from ..types import Chat, BlacklistItem, Template, BannedUser

class Banlist(AbstractTable):
    async def get(self, uid) -> BannedUser:
        return await self.db.banlist.get_user(uid)

    async def add(self, uid: int, reason: str) -> BannedUser:
        return await self.db.banlist.add_user(uid, reason)

    async def remove(self, uid: int) -> None:
        return await self.db.banlist.remove(uid)

    async def get_multiple(self, ids) -> List[BannedUser]:
        return await self.db.banlist.get_multiple(ids)

    async def count_reason(self, reason) -> int:
        reason = self.db.convert_wildcard(reason)
        return await self.db.banlist.count_reason(reason)

    async def get_with_reason(self, reason) -> List[BannedUser]:
        reason = self.db.convert_wildcard(reason)
        return await self.db.banlist.get_with_reason(reason)

    async def total_count(self) -> int:
        return await self.db.banlist.total_count()

    async def upsert_multiple(self, bans: List[Dict[str, str]]) -> None:
        return await self.db.banlist.upsert_multiple(bans)

    async def get_all(self) -> List[BannedUser]:
        return await self.db.banlist.get_all()

    async def get_all_not_in(self, not_in) -> List[BannedUser]:
        return await self.db.banlist.get_all_not_in(not_in)
