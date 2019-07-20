"""Plugin to purge messages up to a specific point"""
import logging

from telethon import events
from telethon.events import NewMessage
from telethon.tl.custom import Message
from telethon.tl.types import Channel

from config import cmd_prefix
from utils.client import KantekClient

__version__ = '0.1.0'

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}purge'))
async def purge(event: NewMessage.Event) -> None:
    """Plugin to purge messages up to a specific point."""
    chat: Channel = await event.get_chat()
    msg: Message = event.message
    client: KantekClient = event.client
    await msg.delete()
    if not msg.is_reply:
        return
    else:
        reply_msg: Message = await msg.get_reply_message()
        await client.delete_messages(chat, list(range(reply_msg.id, msg.id)))
