"""Plugin that automatically bans according to a blacklist"""
import asyncio
import datetime
import itertools
import logging
from typing import Dict

import logzero
from pyArango.theExceptions import DocumentNotFoundError
from telethon import events
from telethon.events import ChatAction, NewMessage
from telethon.tl.custom import MessageButton
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.patched import Message
from telethon.tl.types import (Channel, ChatBannedRights,
                               MessageEntityTextUrl, UserFull, MessageEntityUrl, MessageEntityMention)

from database.arango import ArangoDB
from utils import helpers, constants
from utils.client import KantekClient

__version__ = '0.3.4'

tlog = logging.getLogger('kantek-channel-log')
logger: logging.Logger = logzero.logger


@events.register(events.MessageEdited(outgoing=False))
@events.register(events.NewMessage(outgoing=False))
async def polizei(event: NewMessage.Event) -> None:
    """Plugin to automatically ban users for certain messages."""
    client: KantekClient = event.client
    chat: Channel = await event.get_chat()
    db: ArangoDB = client.db
    chat_document = db.groups.get_chat(event.chat_id)
    db_named_tags: Dict = chat_document['named_tags'].getStore()
    bancmd = db_named_tags.get('gbancmd')
    polizei_tag = db_named_tags.get('polizei')
    if polizei_tag == 'exclude':
        return
    ban_type, ban_reason = await _check_message(event)
    if ban_type and ban_reason:
        await _banuser(event, chat, event.message.from_id, bancmd, ban_type, ban_reason)


@events.register(events.chataction.ChatAction())
async def biopolizei(event: ChatAction.Event) -> None:
    """Plugin to ban users with blacklisted strings in their bio."""
    client: KantekClient = event.client
    chat: Channel = await event.get_chat()
    db: ArangoDB = client.db
    chat_document = db.groups.get_chat(event.chat_id)
    db_named_tags: Dict = chat_document['named_tags'].getStore()
    bancmd = db_named_tags.get('gbancmd')
    polizei_tag = db_named_tags.get('polizei')
    if polizei_tag == 'exclude':
        return
    ban_type, ban_reason = False, False
    bio_blacklist = db.ab_bio_blacklist.get_all()
    try:
        user: UserFull = await client(GetFullUserRequest(await event.get_input_user()))
    except TypeError as e:
        logger.error(e)
        return

    for string in bio_blacklist:
        if user.about and string in user.about:
            ban_type, ban_reason = db.ab_bio_blacklist.hex_type, bio_blacklist[string]
    if ban_type and ban_reason:
        await _banuser(event, chat, event.user_id, bancmd, ban_type, ban_reason)


async def _banuser(event, chat, userid, bancmd, ban_type, ban_reason):
    formatted_reason = f'Spambot[kv2 {ban_type} 0x{ban_reason.rjust(4, "0")}]'
    client: KantekClient = event.client
    db: ArangoDB = client.db
    await event.delete()
    try:
        old_ban_reason = db.banlist[userid]['reason']
        if old_ban_reason == formatted_reason:
            logger.info(f'User ID `{userid}` already banned for the same reason.')
            return
    except DocumentNotFoundError:
        pass
    if chat.creator or chat.admin_rights:
        if bancmd == 'manual':
            await client(EditBannedRequest(
                chat, userid, ChatBannedRights(
                    until_date=datetime.datetime(2038, 1, 1),
                    view_messages=True
                )
            ))
        elif bancmd is not None:
            await client.respond(event, f'{bancmd} {userid} {formatted_reason}')
            await asyncio.sleep(0.25)
    await client.gban(userid, formatted_reason)


async def _check_message(event):
    client: KantekClient = event.client
    msg: Message = event.message
    # exclude users below a certain id to avoid banning "legit" users
    if msg.from_id and msg.from_id < 610000000:
        return False, False

    # disabled until the admins are cached to avoid fetching them on every message
    # admins = [p.id for p in (await client.get_participants(event.chat_id,
    #                                                        filter=ChannelParticipantsAdmins()))]
    # if msg.from_id in admins:
    #     return False, False

    # commands used in bots to blacklist items, these will be used by admins
    # so they shouldnt be banned for it
    blacklisting_commands = [
        '/addblacklist',
    ]
    for cmd in blacklisting_commands:
        if msg.text and msg.text.startswith(cmd):
            return False, False

    db: ArangoDB = client.db
    string_blacklist = db.ab_string_blacklist.get_all()
    channel_blacklist = db.ab_channel_blacklist.get_all()
    domain_blacklist = db.ab_domain_blacklist.get_all()

    if msg.buttons:
        _buttons = await msg.get_buttons()
        button: MessageButton
        for button in itertools.chain.from_iterable(_buttons):
            if button.url:
                _, chat_id, _ = await helpers.resolve_invite_link(button.url)
                if chat_id in channel_blacklist:
                    return db.ab_channel_blacklist.hex_type, channel_blacklist[chat_id]
                domain = await helpers.resolve_url(button.url)
                if domain in domain_blacklist:
                    return db.ab_domain_blacklist.hex_type, domain_blacklist[domain]

    entities = [e for e in msg.get_entities_text()]
    for entity, text in entities:
        link_creator, chat_id, random_part = await helpers.resolve_invite_link(text)
        if chat_id in channel_blacklist.keys():
            return db.ab_channel_blacklist.hex_type, channel_blacklist[chat_id]

        domain = ''
        channel = ''
        _entity = None
        try:
            if isinstance(entity, MessageEntityUrl):
                domain = await helpers.resolve_url(text)
                if domain in constants.TELEGRAM_DOMAINS:
                    _entity = await client.get_cached_entity(text)
            elif isinstance(entity, MessageEntityTextUrl):
                domain = await helpers.resolve_url(entity.url)
                if domain in constants.TELEGRAM_DOMAINS:
                    _entity = await client.get_cached_entity(text)
            elif isinstance(entity, MessageEntityMention):
                _entity = await client.get_cached_entity(text)
        except constants.GET_ENTITY_ERRORS as err:
            logger.error(err)

        if _entity:
            channel = _entity.id

        if domain and domain in domain_blacklist:
            return db.ab_domain_blacklist.hex_type, domain_blacklist[domain]
        if channel and channel in channel_blacklist:
            return db.ab_channel_blacklist.hex_type, channel_blacklist[channel]

    for string in string_blacklist:
        if string in msg.raw_text:
            return db.ab_string_blacklist.hex_type, string_blacklist[string]

    return False, False
