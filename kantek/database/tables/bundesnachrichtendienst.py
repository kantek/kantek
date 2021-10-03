from typing import Optional, List

from . import AbstractTable
from ..types import BNDAction, CharacterClass, BND


class Bundesnachrichtendienst(AbstractTable):
    async def add(self, chat_id: int, action: BNDAction,
                  pattern: Optional[str] = None, character_class: Optional[CharacterClass] = None) -> BND:
        return await self.db.bundesnachrichtendienst.add(chat_id, action, pattern, character_class)

    async def get(self, uid: int) -> BND:
        return await self.db.bundesnachrichtendienst.get(uid)

    async def get_all_for_chat(self, uid: int) -> List[BND]:
        return await self.db.bundesnachrichtendienst.get_all_for_chat(uid)

    async def edit(self, uid: int, action: BNDAction,
                   pattern: Optional[str] = None, character_class: Optional[CharacterClass] = None) -> Optional[BND]:
        return await self.db.bundesnachrichtendienst.edit(uid, action, pattern, character_class)

    async def remove(self, uid: int) -> None:
        return await self.db.bundesnachrichtendienst.remove(uid)

