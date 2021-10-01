import secrets
from typing import Optional

from . import AbstractTable
from ..types import Chat, BlacklistItem, Template, BannedUser
class Strafanzeigen(AbstractTable):
    async def add(self, content) -> str:
        key = secrets.token_urlsafe(10)
        return await self.db.strafanzeigen.add(content, key)

    async def get(self, sa_key) -> Optional[str]:
        return await self.db.strafanzeigen.get(sa_key)

    async def cleanup(self):
        await self.db.strafanzeigen.cleanup()

