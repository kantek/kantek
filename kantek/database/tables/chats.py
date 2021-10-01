from typing import Dict

from . import AbstractTable
from ..types import Chat, BlacklistItem, Template, BannedUser
class Chats(AbstractTable):
    async def add(self, chat_id: int) -> Chat:
        return await self.db.chats.add(chat_id)

    async def get(self, chat_id: int) -> Chat:
        return await self.db.chats.get(chat_id)

    async def lock(self, chat_id: int, permissions: Dict[str, bool]):
        await self.db.chats.lock(chat_id, permissions)

    async def unlock(self, chat_id: int):
        await self.db.chats.unlock(chat_id)

    async def update_tags(self, chat_id: int, new: Dict):
        return await self.db.chats.update_tags(chat_id, new)

