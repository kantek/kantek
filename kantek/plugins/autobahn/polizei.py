"""Plugin that automatically bans according to a blacklist"""
import logging
from typing import Dict, List

from telethon import events, utils
from telethon.events import NewMessage
from telethon.tl.patched import Message
from telethon.tl.types import Channel, User

from config import cmd_prefix
from database.arango import ArangoDB
from utils import helpers
from utils.client import KantekClient
from utils.mdtex import Bold, Code, Item, KeyValueItem, MDTeXDocument, Section

__version__ = '0.1.0'

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage(chats=[-1001129887931]))
async def polizei(event: NewMessage.Event) -> None:
    """Plugin to automatically ban users for certain messages."""
    client: KantekClient = event.client
    chat: Channel = event.chat
    db: ArangoDB = client.db
    chat_document = db.groups.get_chat(event.chat_id)
    db_named_tags: Dict = chat_document['named_tags'].getStore()
    db_tags: List = chat_document['tags']
    polizei_tag = db_named_tags.get('polizei')
    if polizei_tag == 'exclude':
        return
    print('-' * 10)
    msg: Message = event.message
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

    if ban_type and ban_reason:
        if chat.creator or chat.admin_rights:
            await msg.delete()
        await client.gban(msg.from_id, f'Spambot[kv2 {ban_type} 0x{ban_reason.rjust(4, "0")}]')



