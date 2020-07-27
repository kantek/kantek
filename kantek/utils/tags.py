from typing import Optional, Union

from telethon.events import NewMessage

from database.arango import ArangoDB

TagValue = Union[bool, str, int]
TagName = Union[int, str]


class Tags:
    """Class to manage the tags of a chat"""

    def __init__(self, event: NewMessage.Event):
        db: ArangoDB = event.client.db
        collection = db.chats

        if not event.is_private:
            self._document = collection.get_chat(event.chat_id)
            self.named_tags = self._document['named_tags'].getStore()
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

    def __getitem__(self, item: TagName) -> TagValue:
        return self.get(item)

    def set(self, tag_name: TagName, value: Optional[TagValue]) -> None:
        """Set a tags value or create it.
        If value is None a normal tag will be created. If the value is not None a named tag with
         that value will be created
        Args:
            tag_name: Name of the tag
            value: The value of the tag

        Returns: None

        """
        self.named_tags[tag_name] = value
        self._save()

    def __setitem__(self, key: TagName, value: TagValue) -> None:
        self.set(key, value)

    def clear(self) -> None:
        """Clears all tags that a Chat has."""
        self._document['named_tags'] = {}
        self._document.save()

    def remove(self, tag_name: TagName) -> None:
        """Delete a tag.

        Args:
            tag_name: Name of the tag

        Returns: None

        """
        if tag_name in self.named_tags:
            del self.named_tags[tag_name]
        self._save()

    def __delitem__(self, key: TagName) -> None:
        self.remove(key)

    def _save(self):
        self._document['named_tags'] = self.named_tags
        self._document.save()
