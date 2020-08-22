import asyncio
import itertools
import logging

import logzero
from PIL import UnidentifiedImageError
from photohash import hashes_are_similar
from telethon import events
from telethon.errors import UserNotParticipantError, ChannelPrivateError, FloodWaitError
from telethon.events import ChatAction, NewMessage
from telethon.tl.custom import Message
from telethon.tl.custom import MessageButton
from telethon.tl.functions.channels import DeleteUserHistoryRequest, GetParticipantRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import (Channel, MessageEntityTextUrl, UserFull, MessageEntityUrl,
                               MessageEntityMention, ChannelParticipantsAdmins, ChannelParticipantAdmin)

from database.database import Database
from utils import helpers, constants
from utils.client import Client
from utils.constants import GET_ENTITY_ERRORS
from utils.helpers import hash_photo
from utils.pluginmgr import k
from utils.tags import Tags

tlog = logging.getLogger('kantek-channel-log')
logger: logging.Logger = logzero.logger


@k.event(events.MessageEdited(outgoing=False))
@k.event(events.NewMessage(outgoing=False), name='polizei')
async def polizei(event: NewMessage.Event) -> None:
    """Checks every message against the autobahn blacklists and bans a user if necessary

    If the message comes from an admin or a bot it is ignored.

    The user will be banned with a reason that contains the blacklist and the index of the blacklisted item. The message is automatically submitted to the SpamWatch API if applicable.

    Tags:
        polizei:
            exclude: Messages won't be checked
    """
    if event.is_private:
        return
    client: Client = event.client
    try:
        chat: Channel = await event.get_chat()
    except ChannelPrivateError:
        return
    tags = await Tags.from_event(event)
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
    # avoid flood waits from chats mass adding users and don't check users leaving
    if not event.user_joined:
        return
    client: Client = event.client
    try:
        chat: Channel = await event.get_chat()
    except ChannelPrivateError:
        return
    db: Database = client.db
    tags = await Tags.from_event(event)
    bancmd = tags.get('gbancmd')
    polizei_tag = tags.get('polizei')
    if polizei_tag == 'exclude':
        return
    ban_type, ban_reason = False, False
    bio_blacklist = await db.blacklists.bio.get_all()
    mhash_blacklist = await db.blacklists.mhash.get_all()

    try:
        user: UserFull = await client(GetFullUserRequest(await event.get_input_user()))
    except TypeError as e:
        logger.error(e)
        return

    for item in bio_blacklist:
        if user.about and item.value in user.about and not item.retired:
            ban_type, ban_reason = db.blacklists.bio.hex_type, item.index

    if user.profile_photo:
        try:
            dl_photo = await client.download_file(user.profile_photo)
        except constants.DOWNLOAD_ERRORS:
            dl_photo = None
        if dl_photo:
            photo_hash = await hash_photo(dl_photo)

            for mhash in mhash_blacklist:
                if mhash and not mhash.retired:
                    if hashes_are_similar(mhash.value, photo_hash, tolerance=2):
                        ban_type, ban_reason = db.blacklists.mhash.hex_type, mhash.index

    if ban_type and ban_reason:
        await _banuser(event, chat, event.user_id, bancmd, ban_type, ban_reason)


async def _banuser(event, chat, userid, bancmd, ban_type, ban_reason):
    formatted_reason = f'Spambot[kv2 {ban_type} 0x{str(ban_reason).rjust(4, "0")}]'
    client: Client = event.client
    db: Database = client.db
    chat: Channel = await event.get_chat()
    admin = chat.creator or chat.admin_rights
    await event.delete()
    old_ban = await db.banlist.get(userid)
    if old_ban:
        if old_ban.reason == formatted_reason:
            logger.info('User ID `%s` already banned for the same reason.', userid)
            return
    if admin:
        if bancmd == 'manual':
            await client.ban(chat, userid)
        elif bancmd is not None:
            await client.respond(event, f'{bancmd} {userid} {formatted_reason}')
            await asyncio.sleep(0.25)
    await client.gban(userid, formatted_reason, await helpers.textify_message(event.message))

    message_count = len(await client.get_messages(chat, from_user=userid, limit=10))
    if admin and message_count <= 5:
        await client(DeleteUserHistoryRequest(chat, userid))


async def _check_message(event):  # pylint: disable = R0911
    client: Client = event.client
    msg: Message = event.message
    user_id = msg.from_id
    if user_id is None:
        return False, False

    try:
        result = await client(GetParticipantRequest(event.chat_id, user_id))
        if isinstance(result.participant, ChannelParticipantAdmin):
            return False, False
    except (ValueError, UserNotParticipantError):
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

    db: Database = client.db
    # tld_blacklist = db.ab_tld_blacklist.get_all()

    inline_bot = msg.via_bot_id
    if inline_bot is not None:
        result = await db.blacklists.channel.get_by_value(inline_bot)
        if result:
            return db.blacklists.channel.hex_type, result.index

    if msg.buttons:
        _buttons = await msg.get_buttons()
        button: MessageButton
        for button in itertools.chain.from_iterable(_buttons):
            if button.url:
                _, chat_id, _ = await helpers.resolve_invite_link(button.url)
                result = await db.blacklists.channel.get_by_value(chat_id)
                if result:
                    return db.blacklists.channel.hex_type, result.index

                domain = await client.resolve_url(button.url)
                result = await db.blacklists.domain.get_by_value(domain)
                if result:
                    return db.blacklists.domain.hex_type, result.index

                # tld_index = await _check_tld(domain, tld_blacklist)
                # if tld_index:
                #     return db.ab_tld_blacklist.hex_type, tld_index

                face_domain = await helpers.netloc(button.url)
                result = await db.blacklists.domain.get_by_value(face_domain)
                if result:
                    return db.blacklists.domain.hex_type, result.index

                elif domain in constants.TELEGRAM_DOMAINS:
                    _entity = await client.get_cached_entity(domain)
                    if _entity:
                        result = await db.blacklists.channel.get_by_value(_entity)
                        if result:
                            return db.blacklists.channel.hex_type, result.index

    entities = msg.get_entities_text()
    for entity, text in entities:  # pylint: disable = R1702
        _, chat_id, _ = await helpers.resolve_invite_link(text)
        result = await db.blacklists.channel.get_by_value(chat_id)
        if result:
            return db.blacklists.channel.hex_type, result.index

        domain = ''
        face_domain = ''
        channel = ''
        _entity = None
        if isinstance(entity, MessageEntityUrl):
            try:
                domain = await client.resolve_url(text)
            except ValueError:
                pass
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
                try:
                    full_entity = await client.get_cached_entity(_entity)
                except (FloodWaitError, *GET_ENTITY_ERRORS):
                    full_entity = None
                if full_entity:
                    channel = full_entity.id
                    try:
                        profile_photo = await client.download_profile_photo(full_entity, bytes)
                    except constants.DOWNLOAD_ERRORS:
                        profile_photo = None
                    if profile_photo:
                        try:
                            photo_hash = await hash_photo(profile_photo)
                            for mhash in await db.blacklists.mhash.get_all():
                                if mhash and not mhash.retired:
                                    if hashes_are_similar(mhash.value, photo_hash, tolerance=2):
                                        return db.blacklists.mhash.hex_type, mhash.index
                        except UnidentifiedImageError:
                            pass

            except (*constants.GET_ENTITY_ERRORS, ChannelPrivateError):
                pass

        # urllib doesnt like urls without a protocol
        if not face_domain:
            face_domain = await helpers.netloc(f'http://{domain}')

        if domain:
            result = await db.blacklists.domain.get_by_value(domain)
            if result:
                return db.blacklists.domain.hex_type, result.index
            # else:
            # tld_index = await _check_tld(domain, tld_blacklist)
            # if tld_index:
            #     return db.ab_tld_blacklist.hex_type, tld_index

        if face_domain:
            result = await db.blacklists.domain.get_by_value(face_domain)
            if result:
                return db.blacklists.domain.hex_type, result.index
            # else:
            # tld_index = await _check_tld(face_domain, tld_blacklist)
            # if tld_index:
            #     return db.ab_tld_blacklist.hex_type, tld_index

        if channel:
            result = await db.blacklists.channel.get_by_value(channel)
            if result:
                return db.blacklists.channel.hex_type, result.index

    if msg.raw_text:
        for string in await db.blacklists.string.get_all():
            if string.value in msg.raw_text and not string.retired:
                return db.blacklists.string.hex_type, string.index

    if msg.file:
        # avoid a DoS when getting large files
        ten_mib = (1024 ** 2) * 10
        # Only download files to avoid downloading photos
        if msg.document and msg.file.size < ten_mib:
            try:
                dl_file = await msg.download_media(bytes)
            except constants.DOWNLOAD_ERRORS:
                dl_file = None
            if dl_file:
                filehash = helpers.hash_file(dl_file)
                result = await db.blacklists.file.get_by_value(filehash)
                if result:
                    return db.blacklists.file.hex_type, result.index
        else:
            pass

    if msg.photo:
        try:
            dl_photo = await msg.download_media(bytes)
        except constants.DOWNLOAD_ERRORS:
            dl_photo = None
        if dl_photo:
            try:
                photo_hash = await hash_photo(dl_photo)
            except UnidentifiedImageError:
                photo_hash = None
            if photo_hash:
                for mhash in await db.blacklists.mhash.get_all():
                    if not mhash.retired:
                        if hashes_are_similar(mhash.value, photo_hash, tolerance=2):
                            return db.blacklists.mhash.hex_type, mhash.index

    return False, False

# async def _check_tld(domain, tld_blacklist):
#     domain, tld = domain.split('.')
#     if tld in tld_blacklist and domain != 'nic':
#         return tld_blacklist[tld]
#     else:
#         return False
