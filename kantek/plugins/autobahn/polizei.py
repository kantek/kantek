"""Plugin that automatically bans according to a blacklist"""
import asyncio
import datetime
import logging
from typing import Dict, List

from telethon import events
from telethon.events import NewMessage
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.patched import Message
from telethon.tl.types import (Channel, ChannelParticipantsAdmins, ChatBannedRights,
                               MessageEntityTextUrl)

from database.arango import ArangoDB
from utils import helpers
from utils.client import KantekClient

__version__ = '0.1.0'

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage(outgoing=True))
async def polizei(event: NewMessage.Event) -> None:
    """Plugin to automatically ban users for certain messages."""
    client: KantekClient = event.client
    chat: Channel = await event.get_chat()
    db: ArangoDB = client.db
    chat_document = db.groups.get_chat(event.chat_id)
    db_named_tags: Dict = chat_document['named_tags'].getStore()
    bancmd = db_named_tags.get('gbancmd')
    db_tags: List = chat_document['tags']
    polizei_tag = db_named_tags.get('polizei')
    if polizei_tag == 'exclude':
        return
    ban_type, ban_reason = await _check_message(event)

    if ban_type and ban_reason:
        msg: Message = event.message
        if chat.creator or chat.admin_rights:
            await msg.delete()
        if chat.creator or chat.admin_rights:
            if bancmd == 'manual':
                await client(EditBannedRequest(
                    chat, msg.from_id, ChatBannedRights(
                        until_date=datetime.datetime(2038, 1, 1),
                        view_messages=True
                    )
                ))
            elif bancmd is not None:
                await msg.reply(f'{bancmd} {ban_reason}')
                await asyncio.sleep(0.25)
            await msg.delete()
        await client.gban(msg.from_id, f'Spambot[kv2 {ban_type} 0x{ban_reason.rjust(4, "0")}]')


async def _check_message(event):
    client: KantekClient = event.client
    msg: Message = event.message
    # exclude users below a certain id to avoid banning "legit" users
    if msg.from_id < 610000000:
        return False, False

    admins = [p.id for p in (await client.get_participants(event.chat_id,
                                                           filter=ChannelParticipantsAdmins()))]
    if msg.from_id in admins:
        return False, False

    db: ArangoDB = client.db
    bio_blacklist = db.ab_bio_blacklist.get_all()
    string_blacklist = db.ab_string_blacklist.get_all()
    filename_blacklist = db.ab_filename_blacklist.get_all()
    channel_blacklist = db.ab_channel_blacklist.get_all()
    ban_type = False
    ban_reason = False
    entities = (e[1] for e in msg.get_entities_text())
    for e in entities:
        link_creator, chat_id, random_part = await helpers.resolve_invite_link(e)
        if chat_id in channel_blacklist.keys():
            ban_type = db.ab_channel_blacklist.hex_type
            ban_reason = channel_blacklist[chat_id]

    for string in string_blacklist:
        if string in msg.raw_text:
            ban_type = db.ab_string_blacklist.hex_type
            ban_reason = string_blacklist[string]

    if ban_type and ban_reason:
        if chat.creator or chat.admin_rights:
            await msg.delete()
        await client.gban(msg.from_id, f'Spambot[kv2 {ban_type} 0x{ban_reason.rjust(4, "0")}]')
