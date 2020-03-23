"""Plugin to delete a message"""
import logging

from telethon import events
from telethon.events import NewMessage
from telethon.tl.patched import Message
from telethon.tl.types import Channel

from config import cmd_prefix
from utils.client import KantekClient

__version__ = '0.1.0'

from utils.constants import SCHEDULE_DELETION_COMMAND

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage(outgoing=True, pattern=SCHEDULE_DELETION_COMMAND))
async def delete(event: NewMessage.Event) -> None:
    """Delete the replied to message

    Args:
        event: The event of the command

    Returns: None

    """
    msg: Message = event.message
    await msg.delete()
    if msg.is_reply:
        reply_msg: Message = await msg.get_reply_message()
        await reply_msg.delete()
