from builtins import int
from typing import Optional, Union

from telethon.events import NewMessage

from ..database import Database

TagValue = Union[bool, str, int]
TagName = Union[int, str]


class Tags:
    """Class to manage the tags of a chat"""

    def __init__(self, db: Database, chat_id, private):
        self.db = db
        self.chat_id = chat_id
        self.private = private

    @classmethod
    async def from_event(cls, event: NewMessage.Event) -> 'Tags':
        tags = Tags(event.client.db, event.chat_id, event.is_private)
        await tags.setup()
        return tags

    @classmethod
    async def from_id(cls, db: Database, chat_id, private) -> 'Tags':
        tags = Tags(db, chat_id, private)
        await tags.setup()
        return tags

    async def setup(self):
        if not self.private:
            chat = await self.db.chats.get(self.chat_id)
            if not chat:
                chat = await self.db.chats.add(self.chat_id)
            self.named_tags = chat.tags
        else:
            self.named_tags = {
                "polizei": "exclude"
            }

    def get(self, tag_name: TagName, default: TagValue = None) -> Optional[TagValue]:
        """Get a Tags Value

        Args:
            tag_name: Name of the tag
            default: Default value to return if the tag does not exist

        Returns:
            The tags value for named tags
            True if the tag exists
            None if the tag doesn't exist

        """
        return self.named_tags.get(tag_name, default)

    async def set(self, tag_name: TagName, value: Optional[TagValue]) -> None:
        """Set a tags value or create it.
        If value is None a normal tag will be created. If the value is not None a named tag with
         that value will be created
        Args:
            tag_name: Name of the tag
            value: The value of the tag

        Returns: None

        """
        self.named_tags[tag_name] = value
        await self._save()

    async def remove(self, tag_name: TagName) -> None:
        """Delete a tag.

        Args:
            tag_name: Name of the tag

        Returns: None

        """
        if tag_name in self.named_tags:
            del self.named_tags[tag_name]
        await self._save()

    async def clear(self) -> None:
        """Clears all tags that a Chat has."""
        self.named_tags = {}
        await self._save()

    async def _save(self):
        await self.db.chats.update_tags(self.chat_id, self.named_tags)
