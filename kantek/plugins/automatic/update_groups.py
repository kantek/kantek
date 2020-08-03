import logging

from telethon import events
from telethon.events import NewMessage

from utils.client import Client
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.event(events.NewMessage())
async def add_groups(event: NewMessage.Event) -> None:
    if event.is_private:
        return
    client: Client = event.client
    await client.db.cleanup()
    await client.db.chats.get(event.chat_id)
