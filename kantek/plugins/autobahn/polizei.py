"""Plugin that automatically bans according to a blacklist"""
import asyncio
import datetime
import itertools
import logging
import os
import uuid
from typing import Dict

import logzero
from pyArango.theExceptions import DocumentNotFoundError
from telethon import events
from telethon.events import ChatAction, NewMessage
from telethon.tl.custom import Message
from telethon.tl.custom import MessageButton
from telethon.tl.functions.channels import EditBannedRequest, DeleteUserHistoryRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import (Channel, ChatBannedRights,
                               MessageEntityTextUrl, UserFull, MessageEntityUrl,
                               MessageEntityMention, Photo)

from database.arango import ArangoDB
from utils import helpers, constants
from utils.client import KantekClient
from utils.helpers import hash_photo
from photohash import hashes_are_similar

__version__ = '0.4.1'

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
    bancmd = db_named_tags.get('gbancmd', 'manual')
    polizei_tag = db_named_tags.get('polizei')
    if polizei_tag == 'exclude':
        return
    ban_type, ban_reason = await _check_message(event)
    if ban_type and ban_reason:
        await _banuser(event, chat, event.message.from_id, bancmd, ban_type, ban_reason)


@events.register(events.chataction.ChatAction())
async def join_polizei(event: ChatAction.Event) -> None:
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
    mhash_blacklist = db.ab_mhash_blacklist.get_all()

    try:
        user: UserFull = await client(GetFullUserRequest(await event.get_input_user()))
    except TypeError as e:
        logger.error(e)
        return

    for string in bio_blacklist:
        if user.about and string in user.about:
            ban_type, ban_reason = db.ab_bio_blacklist.hex_type, bio_blacklist[string]

    if user.profile_photo:
        dl_photo = await client.download_file(user.profile_photo)
        photo_hash = await hash_photo(dl_photo)

        for mhash in mhash_blacklist:
            if hashes_are_similar(mhash, photo_hash, tolerance=2):
                ban_type, ban_reason = db.ab_mhash_blacklist.hex_type, mhash_blacklist[mhash]

    if ban_type and ban_reason:
        await _banuser(event, chat, event.user_id, bancmd, ban_type, ban_reason)


async def _banuser(event, chat, userid, bancmd, ban_type, ban_reason):
    formatted_reason = f'Spambot[kv2 {ban_type} 0x{ban_reason.rjust(4, "0")}]'
    client: KantekClient = event.client
    db: ArangoDB = client.db
    chat: Channel = await event.get_chat()
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

    message_count = len(await client.get_messages(chat, from_user=userid, limit=10))
    if message_count <= 5:
        await client(DeleteUserHistoryRequest(chat, userid))


async def _check_message(event):
    client: KantekClient = event.client
    msg: Message = event.message
    user_id = msg.from_id
    if user_id is None:
        return False, False
    # exclude users below a certain id to avoid banning "legit" users
    if user_id and user_id < 610000000:
        return False, False

    # no need to ban bots as they can only be added by users anyway
    user = await client.get_cached_entity(user_id)
    if user.bot:
        return False, False

    # disabled until the admins are cached to avoid fetching them on every message
    # admins = [p.id for p in (await client.get_participants(event.chat_id,
    #                                                        filter=ChannelParticipantsAdmins()))]
    # if user_id in admins:
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
    file_blacklist = db.ab_file_blacklist.get_all()
    mhash_blacklist = db.ab_mhash_blacklist.get_all()

    inline_bot = msg.via_bot_id
    if inline_bot is not None and inline_bot in channel_blacklist:
        return db.ab_channel_blacklist.hex_type, channel_blacklist[inline_bot]

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
                face_domain = await helpers.netloc(button.url)
                if face_domain in domain_blacklist:
                    return db.ab_domain_blacklist.hex_type, domain_blacklist[face_domain]
                elif domain in constants.TELEGRAM_DOMAINS:
                    _entity = await client.get_cached_entity(domain)
                    if _entity and _entity in channel_blacklist:
                        return db.ab_channel_blacklist.hex_type, channel_blacklist[_entity]

    entities = [e for e in msg.get_entities_text()]
    for entity, text in entities:
        link_creator, chat_id, random_part = await helpers.resolve_invite_link(text)
        if chat_id in channel_blacklist.keys():
            return db.ab_channel_blacklist.hex_type, channel_blacklist[chat_id]

        domain = ''
        face_domain = ''
        channel = ''
        _entity = None
        if isinstance(entity, MessageEntityUrl):
            domain = await helpers.resolve_url(text)
            face_domain = await helpers.netloc(text)
            if domain in constants.TELEGRAM_DOMAINS:
                # remove any query parameters like ?start=
                # replace @ since some spammers started using it, only Telegram X supports it
                username = text.split('?')[0].replace('@', '')
                _entity = username

        elif isinstance(entity, MessageEntityTextUrl):
            domain = await helpers.resolve_url(entity.url)
            face_domain = await helpers.netloc(entity.url)
            if domain in constants.TELEGRAM_DOMAINS:
                username = entity.url.split('?')[0].replace('@', '')
                _entity = username
        elif isinstance(entity, MessageEntityMention):
            _entity = text

        if _entity:
            try:
                channel = (await client.get_cached_entity(_entity)).id
            except constants.GET_ENTITY_ERRORS as err:
                logger.error(err)

        if domain and domain in domain_blacklist:
            return db.ab_domain_blacklist.hex_type, domain_blacklist[domain]
        if face_domain and face_domain in domain_blacklist:
            return db.ab_domain_blacklist.hex_type, domain_blacklist[face_domain]
        if channel and channel in channel_blacklist:
            return db.ab_channel_blacklist.hex_type, channel_blacklist[channel]

    for string in string_blacklist:
        if string in msg.raw_text:
            return db.ab_string_blacklist.hex_type, string_blacklist[string]

    if msg.file:
        # avoid a DoS when getting large files
        ten_mib = (1024 ** 2) * 10
        # Only download files to avoid downloading photos
        if msg.document and msg.file.size < ten_mib:
            dl_filename = await msg.download_media(f'tmp/{uuid.uuid4()}')
            filehash = await helpers.hash_file(dl_filename)
            os.remove(dl_filename)
            if filehash in file_blacklist:
                return db.ab_file_blacklist.hex_type, file_blacklist[filehash]
        else:
            logger.warning('Skipped file because it was too large or not a document')

    if msg.photo:
        dl_photo = await msg.download_media(bytes)
        photo_hash = await hash_photo(dl_photo)

        for mhash in mhash_blacklist:
            if hashes_are_similar(mhash, photo_hash, tolerance=2):
                return db.ab_mhash_blacklist.hex_type, mhash_blacklist[mhash]

    return False, False
