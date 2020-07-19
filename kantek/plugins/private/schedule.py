"""Plugin to schedule gbans from a file."""
import logging
from datetime import datetime, timedelta

from telethon import events
from telethon.events import NewMessage
from telethon.tl.functions.messages import GetScheduledHistoryRequest, DeleteScheduledMessagesRequest
from telethon.tl.patched import Message
from telethon.tl.types import Channel, MessageMediaDocument

from config import cmd_prefix
from utils import helpers
from utils.client import KantekClient

__version__ = '0.1.0'

from utils.mdtex import Bold, Code, KeyValueItem, MDTeXDocument, Section

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}schedule'))
async def schedule(event: NewMessage.Event) -> None:
    """Schedule gbans from a file

    Args:
        event: The event of the command

    Returns: None

    """
    client: KantekClient = event.client
    msg = event.message
    chat: Channel = await event.get_chat()

    keyword_args, _ = await helpers.get_args(event)
    offset = keyword_args.get('offset', 1)
    if keyword_args['overwrite']:
        scheduled = await client(GetScheduledHistoryRequest(chat, 0))
        scheduled_ids = [smsg.id for smsg in scheduled.messages]
        await client(DeleteScheduledMessagesRequest(chat, scheduled_ids))

    if msg.is_reply:
        reply_msg: Message = await msg.get_reply_message()
        if isinstance(reply_msg.media, MessageMediaDocument):
            commands = (await reply_msg.download_media(bytes)).decode().split('\n')
        else:
            commands = reply_msg.text.split('\n')
        current = datetime.now()
        next_time = datetime(current.year, current.month, current.day, current.hour + 1, 0, 0)
        from_time = next_time
        for cmd in commands:
            if cmd:
                await client.send_message(chat, cmd, schedule=next_time)
                next_time += timedelta(hours=offset)
        await client.respond(event,
                             MDTeXDocument(
                                 Section(Bold('Scheduled Messages'),
                                         KeyValueItem(Bold('From'), from_time),
                                         KeyValueItem(Bold('To'), next_time),
                                         KeyValueItem(Bold('Count'), Code(len(commands)))
                                         ))
                             )
    await event.delete()
