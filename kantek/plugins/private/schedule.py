"""Plugin to schedule gbans from a file."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict

from telethon.tl.functions.messages import GetScheduledHistoryRequest, DeleteScheduledMessagesRequest
from telethon.tl.patched import Message
from telethon.tl.types import Channel, MessageMediaDocument

from utils.client import KantekClient
from utils.mdtex import Bold, Code, KeyValueItem, MDTeXDocument, Section
from utils.pluginmgr import k, Command

tlog = logging.getLogger('kantek-channel-log')


@k.command('schedule')
async def schedule(client: KantekClient, chat: Channel, msg: Message, kwargs: Dict, event: Command) -> None:
    """Schedule gbans from a file

    Args:
        event: The event of the command

    Returns: None

    """
    offset = kwargs.get('offset', 60)
    dynamic = kwargs.get('dynamic', False)
    if kwargs.get('overwrite'):
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
        next_time = datetime(current.year, current.month,
                             current.day, current.hour, 0, 0).astimezone(timezone.utc)
        next_time += timedelta(hours=1)
        from_time = next_time
        for cmd in commands:
            if cmd:
                if dynamic:
                    offset = len(cmd.split()) ** 0.7
                await client.send_message(chat, cmd, schedule=next_time)
                next_time += timedelta(minutes=offset)
                await asyncio.sleep(0.5)
        await client.respond(
            event,
            MDTeXDocument(
                Section(Bold('Scheduled Messages'),
                        KeyValueItem(Bold('From'),
                                     from_time.astimezone(current.tzinfo).strftime('%Y-%m-%d %H:%M:%S')),
                        KeyValueItem(Bold('To'),
                                     next_time.astimezone(current.tzinfo).strftime('%Y-%m-%d %H:%M:%S')),
                        KeyValueItem(Bold('Count'), Code(len(commands)))
                        ))
        )
    await event.delete()
