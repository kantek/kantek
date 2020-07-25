"""Plugin to get information about a user."""
import logging
from typing import Union, Dict, List

from spamwatch.types import Permission
from telethon.tl.custom import Forward, Message
from telethon.tl.types import MessageEntityMention, MessageEntityMentionName, User, Channel

from database.arango import ArangoDB
from utils import helpers, constants
from utils.client import KantekClient
from utils.mdtex import *
from utils.pluginmgr import k, Command
from utils.tagmgr import TagManager

tlog = logging.getLogger('kantek-channel-log')


@k.command('u(ser)?')
async def user_info(client: KantekClient, msg: Message, tags: TagManager,
                    args: List, kwargs: Dict, event: Command) -> MDTeXDocument:
    """Show information about a user.

    Args:
        client:
        msg:
        args:
        kwargs:
        event:

    """
    # crude hack until I have a proper way to have commands with short options
    # without this ungban will always trigger user too
    if 'ungban' in msg.text:
        return
    if not args and msg.is_reply:
        return await _info_from_reply(event, tags, **kwargs)
    elif args:
        return await _info_from_arguments(event)


async def _info_from_arguments(event) -> MDTeXDocument:
    msg: Message = event.message
    client: KantekClient = event.client
    keyword_args, args = await helpers.get_args(event)
    gban_format = keyword_args.get('gban', False)
    entities = []
    for entity in msg.get_entities_text():
        obj, text = entity
        if isinstance(obj, MessageEntityMentionName):
            entities.append(obj.user_id)
        elif isinstance(obj, MessageEntityMention):
            entities.append(text)
    # append any user ids to the list
    for uid in args:
        if isinstance(uid, int):
            entities.append(uid)

    users = []
    errors = []
    for entity in entities:
        try:
            user: User = await client.get_entity(entity)
            if isinstance(user, Channel):
                errors.append(str(entity))
                continue
            users.append(str(await _collect_user_info(client, user, **keyword_args)))
        except constants.GET_ENTITY_ERRORS:
            errors.append(str(entity))
    if users and gban_format:
        users = [Code(' '.join(users))]
    if users or errors:
        return MDTeXDocument(*users, (Section(Bold('Errors for'), Code(', '.join(errors)))) if errors else '')


async def _info_from_reply(event, tags, **kwargs) -> MDTeXDocument:
    msg: Message = event.message
    client: KantekClient = event.client
    db: ArangoDB = client.db
    get_forward = kwargs.get('forward', True)
    anzeige = tags.get('strafanzeige', False)

    reply_msg: Message = await msg.get_reply_message()

    if get_forward and reply_msg.forward is not None:
        forward: Forward = reply_msg.forward
        if forward.sender_id is None:
            return MDTeXDocument(Section(Bold('Error'), 'User has forward privacy enabled'))
        user: User = await client.get_entity(forward.sender_id)
    else:
        user: User = await client.get_entity(reply_msg.sender_id)
    user_section = await _collect_user_info(client, user, **kwargs)
    if anzeige and isinstance(user_section, Section):
        data = await helpers.create_strafanzeige(user.id, reply_msg)
        key = db.strafanzeigen.add(data)
        user_section.append(SubSection(Bold('Strafanzeige'), KeyValueItem('code', Code(f'sa: {key}'))))
    return MDTeXDocument(user_section)


async def _collect_user_info(client, user, **kwargs) -> Union[str, Section, KeyValueItem]:
    id_only = kwargs.get('id', False)
    gban_format = kwargs.get('gban', False)
    show_general = kwargs.get('general', True)
    show_bot = kwargs.get('bot', False)
    show_misc = kwargs.get('misc', False)
    show_all = kwargs.get('all', False)
    full_ban_msg = kwargs.get('full', False)
    show_spamwatch = kwargs.get('sw', False)

    if show_all:
        show_general = True
        show_bot = True
        show_misc = True
        show_spamwatch = True

    mention_name = kwargs.get('mention', False)

    full_name = await helpers.get_full_name(user)
    if mention_name:
        title = Link(full_name, f'tg://user?id={user.id}')
    else:
        title = Bold(full_name)

    sw_ban = None
    ban_reason = client.db.banlist.get_user(user.id)
    if ban_reason:
        ban_reason = ban_reason['reason']
        if client.sw and client.sw.permission.value <= Permission.User.value:
            sw_ban = client.sw.get_ban(int(user.id))
            ban_message = sw_ban.message
            if ban_message and not full_ban_msg:
                ban_message = f'{ban_message[:128]}{"[...]" if len(ban_message) > 128 else ""}'

    if id_only:
        return KeyValueItem(title, Code(user.id))
    elif gban_format:
        return str(user.id)
    else:
        general = SubSection(
            Bold('General'),
            KeyValueItem('id', Code(user.id)),
            KeyValueItem('first_name', Code(user.first_name)))
        if user.last_name is not None or show_all:
            general.append(KeyValueItem('last_name', Code(user.last_name)))
        if user.username is not None or show_all:
            general.append(KeyValueItem('username', Code(user.username)))

        if ban_reason and not show_spamwatch:
            general.append(KeyValueItem('ban_reason', Code(ban_reason)))
        elif not show_spamwatch:
            general.append(KeyValueItem('gbanned', Code('False')))
        if sw_ban and not show_spamwatch:
            general.append(KeyValueItem('ban_msg', Code(ban_message)))

        spamwatch = SubSection(Bold('SpamWatch'))
        if sw_ban:
            spamwatch.extend([
                KeyValueItem('reason', Code(sw_ban.reason)),
                KeyValueItem('date', Code(sw_ban.date)),
                KeyValueItem('timestamp', Code(sw_ban.timestamp)),
                KeyValueItem('admin', Code(sw_ban.admin)),
                KeyValueItem('message', Code(ban_message)),
            ])
        else:
            spamwatch.append(KeyValueItem('banned', Code('False')))

        bot = SubSection(
            Bold('Bot'),
            KeyValueItem('bot', Code(user.bot)),
            KeyValueItem('bot_chat_history', Code(user.bot_chat_history)),
            KeyValueItem('bot_info_version', Code(user.bot_info_version)),
            KeyValueItem('bot_inline_geo', Code(user.bot_inline_geo)),
            KeyValueItem('bot_inline_placeholder',
                         Code(user.bot_inline_placeholder)),
            KeyValueItem('bot_nochats', Code(user.bot_nochats)))
        misc = SubSection(
            Bold('Misc'),
            KeyValueItem('mutual_contact', Code(user.mutual_contact)),
            KeyValueItem('restricted', Code(user.restricted)),
            KeyValueItem('restriction_reason', Code(user.restriction_reason)),
            KeyValueItem('deleted', Code(user.deleted)),
            KeyValueItem('verified', Code(user.verified)),
            KeyValueItem('min', Code(user.min)),
            KeyValueItem('lang_code', Code(user.lang_code)))

        return Section(title,
                       general if show_general else None,
                       spamwatch if show_spamwatch else None,
                       misc if show_misc else None,
                       bot if show_bot else None)
