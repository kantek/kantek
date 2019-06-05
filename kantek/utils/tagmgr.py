from typing import Optional, Union

from pyArango.document import DocumentStore
from telethon.events import NewMessage

from database.arango import ArangoDB
from utils.client import KantekClient


class TagManager:
    def __init__(self, event: NewMessage.Event):
        self._client: KantekClient = event.client
        self._db: ArangoDB = self._client.db
        self.chat_id = event.chat_id
        self._collection = self._db.groups
        self._document = self._collection[self.chat_id]
        self._named_tags: DocumentStore = self._document['named_tags']
        self.named_tags = self._document['named_tags'].getStore()
        self.tags = self._document['tags']

    def get_tag(self, tag_name) -> Optional[Union[bool, str, int]]:
        return self.named_tags.get(tag_name, tag_name in self.tags or None)

    def __getitem__(self, item):
        return self.get_tag(item)

    def set_tag(self, tag_name, value=None):
        if value is None:
            if tag_name not in self.tags:
                self.tags.append(tag_name)
                self._document['tags'] = self.tags
        elif value is not None:
            self.named_tags[tag_name] = value
            self._document['named_tags'] = self.named_tags
        self._document.save()

    def __setitem__(self, key, value):
        self.set_tag(key, value)

    def clear(self):
        """Clears all tags that a Chat has."""
        self._document['named_tags'] = {}
        self._document['tags'] = []
        self._document.save()
