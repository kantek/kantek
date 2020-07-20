from typing import Optional, Union

from pyArango.theExceptions import DocumentNotFoundError
from telethon.events import NewMessage

TagValue = Union[bool, str, int]
TagName = Union[int, str]


class TagManager:
    """Class to manage the tags of a chat"""

    def __init__(self, event: NewMessage.Event):
        db = event.client.db
        collection = db.groups
        try:
            self._document = collection[event.chat_id]
            self.named_tags = self._document['named_tags'].getStore()
            self.tags = self._document['tags']
            self.read_only = False
        except DocumentNotFoundError:
            self._document = None
            self.named_tags = {}
            self.tags = {}
            self.read_only = True

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
        return self.named_tags.get(tag_name, tag_name in self.tags or default)

    def __getitem__(self, item: TagName) -> TagValue:
        return self.get(item)

    def set(self, tag_name: TagName, value: Optional[TagValue] = None) -> None:
        """Set a tags value or create it.
        If value is None a normal tag will be created. If the value is not None a named tag with
         that value will be created
        Args:
            tag_name: Name of the tag
            value: The value of the tag

        Returns: None

        """
        if not self.read_only:
            if value is None:
                if tag_name not in self.tags:
                    self.tags.append(tag_name)
            elif value is not None:
                self.named_tags[tag_name] = value
            self._save()

    def __setitem__(self, key: TagName, value: TagValue) -> None:
        self.set(key, value)

    def clear(self) -> None:
        """Clears all tags that a Chat has."""
        self._document['named_tags'] = {}
        self._document['tags'] = []
        self._document.save()

    def remove(self, tag_name: TagName) -> None:
        """Delete a tag.

        Args:
            tag_name: Name of the tag

        Returns: None

        """
        if not self.read_only:
            if tag_name in self.tags:
                del self.tags[self.tags.index(tag_name)]
            elif tag_name in self.named_tags:
                del self.named_tags[tag_name]
            self._save()

    def __delitem__(self, key: TagName) -> None:
        self.remove(key)

    def _save(self):
        self._document['tags'] = self.tags
        self._document['named_tags'] = self.named_tags
        self._document.save()
