"""Plugin to schedule gbans from a file."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict

from telethon.tl.functions.messages import GetScheduledHistoryRequest, DeleteScheduledMessagesRequest
from telethon.tl.patched import Message
from telethon.tl.types import Channel, MessageMediaDocument

from utils.client import Client
from utils.mdtex import *
from utils import parsers
from utils.pluginmgr import k, Command

tlog = logging.getLogger('kantek-channel-log')


@k.command('schedule')
async def schedule(client: Client, chat: Channel, msg: Message, kwargs: Dict, event: Command) -> MDTeXDocument:
    """Schedule commands from a file or a message

    One command per line. Must be in reply to either a message or a file.

    Arguments:
        `-overwrite`: Overwrite all currently scheduled commands
        `-dynamic`: Determine the offset between messages dynamically depending on the messages word count
        `offset`: Offset as duration expression, see `{prefix}help parsers time`

    Examples:
        {cmd} -overwrite
        {cmd} -overwrite -dynamic
        {cmd} -overwrite offset: 30m
    """
    offset = kwargs.get('offset', '1h')
    offset = parsers.time(offset)
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
        next_time = current.astimezone(timezone.utc)
        next_time += timedelta(minutes=5)
        from_time = next_time
        for cmd in commands:
            if cmd:
                if dynamic:
                    offset = (len(cmd.split()) ** 0.7)*60
                await client.send_message(chat, cmd, schedule=next_time)
                next_time += timedelta(seconds=offset)
                await asyncio.sleep(0.5)
        await event.delete()
        return MDTeXDocument(
            Section('Scheduled Messages',
                    KeyValueItem(Bold('From'),
                                 from_time.astimezone(current.tzinfo).strftime('%Y-%m-%d %H:%M:%S')),
                    KeyValueItem(Bold('To'),
                                 next_time.astimezone(current.tzinfo).strftime('%Y-%m-%d %H:%M:%S')),
                    KeyValueItem(Bold('Count'), Code(len(commands)))
                    ))

