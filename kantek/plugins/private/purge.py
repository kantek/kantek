"""Plugin to purge messages up to a specific point"""
import logging

from telethon.events import NewMessage
from telethon.tl.custom import Message
from telethon.tl.types import Channel

from utils.client import KantekClient

__version__ = '0.1.0'

from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.command('purge')
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
