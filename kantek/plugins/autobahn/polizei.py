"""Plugin that automatically bans according to a blacklist"""
import asyncio
import itertools
import logging

import logzero
from PIL import UnidentifiedImageError
from photohash import hashes_are_similar
from pyArango.theExceptions import DocumentNotFoundError
from telethon import events
from telethon.events import ChatAction, NewMessage
from telethon.tl.custom import Message
from telethon.tl.custom import MessageButton
from telethon.tl.functions.channels import DeleteUserHistoryRequest, GetParticipantRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import (Channel, MessageEntityTextUrl, UserFull, MessageEntityUrl,
                               MessageEntityMention, ChannelParticipantsAdmins, ChannelParticipantAdmin)

from database.arango import ArangoDB
from utils import helpers, constants
from utils.client import KantekClient
from utils.helpers import hash_photo
from utils.pluginmgr import k
from utils.tagmgr import TagManager

tlog = logging.getLogger('kantek-channel-log')
logger: logging.Logger = logzero.logger


@k.event(events.MessageEdited(outgoing=False))
@k.event(events.NewMessage(outgoing=False))
async def polizei(event: NewMessage.Event) -> None:
    """Plugin to automatically ban users for certain messages."""
    if event.is_private:
        return
    client: KantekClient = event.client
    chat: Channel = await event.get_chat()
    tags = TagManager(event)
    bancmd = tags.get('gbancmd', 'manual')
    polizei_tag = tags.get('polizei')
    if polizei_tag == 'exclude':
        return
    ban_type, ban_reason = await _check_message(event)
    if ban_type and ban_reason:
        uid = event.message.from_id
        admins = [p.id for p in await client.get_participants(event.chat_id, filter=ChannelParticipantsAdmins())]
        if uid not in admins:
            await _banuser(event, chat, uid, bancmd, ban_type, ban_reason)


@k.event(events.chataction.ChatAction())
async def join_polizei(event: ChatAction.Event) -> None:
    """Plugin to ban users with blacklisted strings in their bio."""
    client: KantekClient = event.client
    chat: Channel = await event.get_chat()
    db: ArangoDB = client.db
    tags = TagManager(event)
    bancmd = tags.get('gbancmd')
    polizei_tag = tags.get('polizei')
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
            logger.info('User ID `%s` already banned for the same reason.', userid)
            return
    except DocumentNotFoundError:
        pass
    if chat.creator or chat.admin_rights:
        if bancmd == 'manual':
            await client.ban(chat, userid)
        elif bancmd is not None:
            await client.respond(event, f'{bancmd} {userid} {formatted_reason}')
            await asyncio.sleep(0.25)
    await client.gban(userid, formatted_reason, await helpers.textify_message(event.message))

    message_count = len(await client.get_messages(chat, from_user=userid, limit=10))
    if message_count <= 5:
        await client(DeleteUserHistoryRequest(chat, userid))


async def _check_message(event):  # pylint: disable = R0911
    client: KantekClient = event.client
    msg: Message = event.message
    user_id = msg.from_id
    if user_id is None:
        return False, False
    # exclude users below a certain id to avoid banning "legit" users
    if user_id and user_id < 610000000:
        return False, False
    try:
        result = await client(GetParticipantRequest(event.chat_id, user_id))
        if isinstance(result.participant, ChannelParticipantAdmin):
            return False, False
    except ValueError:
        return False, False

    # no need to ban bots as they can only be added by users anyway
    user = await client.get_cached_entity(user_id)
    if user is None or user.bot:
        return False, False

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
    # tld_blacklist = db.ab_tld_blacklist.get_all()

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

                domain = await client.resolve_url(button.url)

                if domain in domain_blacklist:
                    return db.ab_domain_blacklist.hex_type, domain_blacklist[domain]

                # tld_index = await _check_tld(domain, tld_blacklist)
                # if tld_index:
                #     return db.ab_tld_blacklist.hex_type, tld_index

                face_domain = await helpers.netloc(button.url)
                if face_domain in domain_blacklist:
                    return db.ab_domain_blacklist.hex_type, domain_blacklist[face_domain]

                elif domain in constants.TELEGRAM_DOMAINS:
                    _entity = await client.get_cached_entity(domain)
                    if _entity and _entity in channel_blacklist:
                        return db.ab_channel_blacklist.hex_type, channel_blacklist[_entity]

    entities = msg.get_entities_text()
    for entity, text in entities:  # pylint: disable = R1702
        _, chat_id, _ = await helpers.resolve_invite_link(text)
        if chat_id in channel_blacklist.keys():
            return db.ab_channel_blacklist.hex_type, channel_blacklist[chat_id]

        domain = ''
        face_domain = ''
        channel = ''
        _entity = None
        if isinstance(entity, MessageEntityUrl):
            domain = await client.resolve_url(text)
            face_domain = await helpers.netloc(text)
            if domain in constants.TELEGRAM_DOMAINS:
                # remove any query parameters like ?start=
                # replace @ since some spammers started using it, only Telegram X supports it
                url = await client.resolve_url(text, base_domain=False)
                username = url.split('?')[0].replace('@', '')
                _entity = username

        elif isinstance(entity, MessageEntityTextUrl):
            domain = await client.resolve_url(entity.url)
            face_domain = await helpers.netloc(entity.url)
            if domain in constants.TELEGRAM_DOMAINS:
                url = await client.resolve_url(entity.url, base_domain=False)
                username = url.split('?')[0].replace('@', '')
                _entity = username

        elif isinstance(entity, MessageEntityMention):
            _entity = text

        if _entity:
            try:
                full_entity = await client.get_cached_entity(_entity)
                if full_entity:
                    channel = full_entity.id
                    profile_photo = await client.download_profile_photo(full_entity, bytes)
                    try:
                        photo_hash = await hash_photo(profile_photo)
                        for mhash in mhash_blacklist:
                            if hashes_are_similar(mhash, photo_hash, tolerance=2):
                                return db.ab_mhash_blacklist.hex_type, mhash_blacklist[mhash]
                    except UnidentifiedImageError:
                        pass

            except constants.GET_ENTITY_ERRORS as err:
                logger.error(err)

        # urllib doesnt like urls without a protocol
        if not face_domain:
            face_domain = await helpers.netloc(f'http://{domain}')

        if domain:
            if domain in domain_blacklist:
                return db.ab_domain_blacklist.hex_type, domain_blacklist[domain]
            # else:
            # tld_index = await _check_tld(domain, tld_blacklist)
            # if tld_index:
            #     return db.ab_tld_blacklist.hex_type, tld_index

        if face_domain:
            if face_domain in domain_blacklist:
                return db.ab_domain_blacklist.hex_type, domain_blacklist[face_domain]
            # else:
            # tld_index = await _check_tld(face_domain, tld_blacklist)
            # if tld_index:
            #     return db.ab_tld_blacklist.hex_type, tld_index

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
            dl_file = await msg.download_media(bytes)
            filehash = helpers.hash_file(dl_file)
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

# async def _check_tld(domain, tld_blacklist):
#     domain, tld = domain.split('.')
#     if tld in tld_blacklist and domain != 'nic':
#         return tld_blacklist[tld]
#     else:
#         return False
