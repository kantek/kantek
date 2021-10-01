from typing import List

from . import AbstractTable
from ..types import Chat, BlacklistItem, Template, BannedUser
class Templates(AbstractTable):
    async def add(self, name: str, content: str, edit: bool) -> Template:
        await self.db.templates.add(name, content, edit)
        return Template(name, content, edit)

    async def get(self, name: str) -> Template:
        return await self.db.templates.get(name)

    async def get_all(self) -> List[Template]:
        return await self.db.templates.get_all()

    async def delete(self, name: str) -> None:
        return await self.db.templates.delete(name)
