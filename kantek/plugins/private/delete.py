"""Plugin to delete a message"""
import logging

from telethon import events
from telethon.events import NewMessage
from telethon.tl.patched import Message

from utils.constants import SCHEDULE_DELETION_COMMAND
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.event(events.NewMessage(outgoing=True, pattern=SCHEDULE_DELETION_COMMAND))
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
