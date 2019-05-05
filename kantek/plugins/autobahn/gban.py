"""Plugin to handle global bans"""
import logging

from telethon import events
from telethon.events import NewMessage
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.patched import Message
from telethon.tl.types import Channel, InputReportReasonSpam

from config import cmd_prefix
from database.arango import ArangoDB
from utils import helpers
from utils.client import KantekClient

__version__ = '0.1.0'

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}gban'))
async def gban(event: NewMessage.Event) -> None:
    """"""

    chat: Channel = event.chat
    msg: Message = event.message
    client: KantekClient = event.client
    db: ArangoDB = client.db
    banlist = db.banlist
    keyword_args, args = await helpers.get_args(event)
    fban = keyword_args.get('fban', True)
    await msg.delete()
    if msg.is_reply:
        reply_msg: Message = await msg.get_reply_message()
        uid = reply_msg.from_id
        if args:
            ban_reason = args[0]
        else:
            ban_reason = 'spam[gban]'
        await client.gban(uid, ban_reason, fedban=fban)
        data = {'_key': str(uid),
                'id': str(uid),
                'reason': ban_reason}
        db.query('UPSERT {"_key": @ban.id} '
                 'INSERT @ban '
                 'UPDATE {"reason": @ban.reason} '
                 'IN BanList', bind_vars={'ban': data})
        await client(ReportRequest(chat, [reply_msg.id], InputReportReasonSpam()))
        if chat.creator or chat.admin_rights:
            await reply_msg.delete()
