import logging

from telethon import events
from telethon.events import NewMessage
from telethon.tl.types import Channel

from kantek import Client
from kantek.utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.event(events.NewMessage())
async def add_groups(event: NewMessage.Event) -> None:
    if event.is_private:
        return
    client: Client = event.client
    await client.db.cleanup()
    c: Channel = event.chat
    await client.db.chats.add(event.chat_id, c.title)
