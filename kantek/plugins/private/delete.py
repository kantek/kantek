import logging

from telethon import events
from telethon.events import NewMessage
from telethon.tl.patched import Message

from utils.constants import SCHEDULE_DELETION_COMMAND
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.event(events.NewMessage(outgoing=True, pattern=SCHEDULE_DELETION_COMMAND))
async def delete(event: NewMessage.Event) -> None:
    """Delete the message that was replied to"""
    msg: Message = event.message
    await msg.delete()
    if msg.is_reply:
        reply_msg: Message = await msg.get_reply_message()
        if reply_msg:
            await reply_msg.delete()
