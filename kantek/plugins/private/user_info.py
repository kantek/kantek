"""Plugin to get information about a user."""
import logging
from typing import Union

from spamwatch.types import Permission
from telethon import events
from telethon.events import NewMessage
from telethon.tl.custom import Forward, Message
from telethon.tl.types import Channel, MessageEntityMention, MessageEntityMentionName, User

from config import cmd_prefix
from utils import helpers, parsers, constants
from utils.client import KantekClient
from utils.mdtex import Bold, Code, KeyValueItem, Link, MDTeXDocument, Section, SubSection

__version__ = '0.1.2'

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}u(ser)?'))
async def user_info(event: NewMessage.Event) -> None:
    """Show information about a user.

    Args:
        event: The event of the command

    Returns: None

    """
    chat: Channel = await event.get_chat()
    client: KantekClient = event.client
    msg: Message = event.message
    # crude hack until I have a proper way to have commands with short options
    # without this ungban will always trigger user too
    if 'ungban' in msg.text:
        return
    _args = msg.raw_text.split()[1:]
    keyword_args, args = parsers.parse_arguments(' '.join(_args))
    response = ''
    if not args and msg.is_reply:
        response = await _info_from_reply(event, **keyword_args)
    elif args or 'search' in keyword_args:
        response = await _info_from_arguments(event)
    if response:
        await client.respond(event, response)


async def _info_from_arguments(event) -> MDTeXDocument:
    msg: Message = event.message
    client: KantekClient = event.client
    keyword_args, args = await helpers.get_args(event)
    search_name = keyword_args.get('search', False)
    gban_format = keyword_args.get('gban', False)
    if search_name:
        entities = [search_name]
    else:
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
            users.append(await _collect_user_info(client, user, **keyword_args))
        except constants.GET_ENTITY_ERRORS as err:
            errors.append(str(entity))
    if users and gban_format:
        users = [Code(' '.join(users))]
    if users or errors:
        return MDTeXDocument(*users, (Section(Bold('Errors for'), Code(', '.join(errors)))) if errors else '')


async def _info_from_reply(event, **kwargs) -> MDTeXDocument:
    msg: Message = event.message
    client: KantekClient = event.client
    get_forward = kwargs.get('forward', True)
    reply_msg: Message = await msg.get_reply_message()

    if get_forward and reply_msg.forward is not None:
        forward: Forward = reply_msg.forward
        if forward.sender_id is None:
            return MDTeXDocument(Section(Bold('Error'), 'User has forward privacy enabled'))
        user: User = await client.get_entity(forward.sender_id)
    else:
        user: User = await client.get_entity(reply_msg.sender_id)

    return MDTeXDocument(await _collect_user_info(client, user, **kwargs))


async def _collect_user_info(client, user, **kwargs) -> Union[Section, KeyValueItem]:
    id_only = kwargs.get('id', False)
    gban_format = kwargs.get('gban', False)
    show_general = kwargs.get('general', True)
    show_bot = kwargs.get('bot', False)
    show_misc = kwargs.get('misc', False)
    show_all = kwargs.get('all', False)
    full_ban_msg = kwargs.get('full', False)

    if show_all:
        show_general = True
        show_bot = True
        show_misc = True

    mention_name = kwargs.get('mention', False)

    full_name = await helpers.get_full_name(user)
    if mention_name:
        title = Link(full_name, f'tg://user?id={user.id}')
    else:
        title = Bold(full_name)

    ban_reason = client.db.banlist.get_user(user.id)
    if ban_reason:
        ban_reason = ban_reason['reason']
        if client.sw and client.sw.permission.value <= Permission.User.value:
            ban = client.sw.get_ban(int(user.id))
            ban_message = ban.message
            if not full_ban_msg:
                ban_message = f'{ban_message[:128]}[...]'

    if id_only:
        return KeyValueItem(title, Code(user.id))
    elif gban_format:
        return str(user.id)
    else:
        general = SubSection(
            Bold('general'),
            KeyValueItem('id', Code(user.id)),
            KeyValueItem('first_name', Code(user.first_name)),
            KeyValueItem('last_name', Code(user.last_name)) if user.last_name is not None or show_all else '',
            KeyValueItem('username', Code(user.username)) if user.username is not None or show_all else '',
            KeyValueItem('ban_reason', Code(ban_reason)) if ban_reason else KeyValueItem('gbanned', Code('False')),
            KeyValueItem('ban_msg', Code(ban_message)) if ban_reason else '')

        bot = SubSection(
            Bold('bot'),
            KeyValueItem('bot', Code(user.bot)),
            KeyValueItem('bot_chat_history', Code(user.bot_chat_history)),
            KeyValueItem('bot_info_version', Code(user.bot_info_version)),
            KeyValueItem('bot_inline_geo', Code(user.bot_inline_geo)),
            KeyValueItem('bot_inline_placeholder',
                         Code(user.bot_inline_placeholder)),
            KeyValueItem('bot_nochats', Code(user.bot_nochats)))
        misc = SubSection(
            Bold('misc'),
            KeyValueItem('mutual_contact', Code(user.mutual_contact)),
            KeyValueItem('restricted', Code(user.restricted)),
            KeyValueItem('restriction_reason', Code(user.restriction_reason)),
            KeyValueItem('deleted', Code(user.deleted)),
            KeyValueItem('verified', Code(user.verified)),
            KeyValueItem('min', Code(user.min)),
            KeyValueItem('lang_code', Code(user.lang_code)))

        return Section(title,
                       general if show_general else None,
                       misc if show_misc else None,
                       bot if show_bot else None)
