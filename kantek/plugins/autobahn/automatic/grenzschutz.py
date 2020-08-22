import logging
from typing import Union

import logzero
from telethon import events
from telethon.errors import UserIdInvalidError, ChannelPrivateError
from telethon.events import ChatAction, NewMessage
from telethon.tl.types import (Channel, ChannelParticipantsAdmins, MessageActionChatJoinedByLink,
                               MessageActionChatAddUser)
from telethon.utils import get_display_name

from database.database import Database
from utils.client import Client
from utils.constants import GET_ENTITY_ERRORS
from kantex.md import *
from utils.pluginmgr import k
from utils.tags import Tags

tlog = logging.getLogger('kantek-channel-log')
logger: logging.Logger = logzero.logger


@k.event(events.chataction.ChatAction())
@k.event(events.NewMessage(), name='grenzschutz')
async def grenzschutz(event: Union[ChatAction.Event, NewMessage.Event]) -> None:  # pylint: disable = R0911
    """Automatically ban gbanned users.

    This plugin will ban gbanned users upon joining,getting added to the group or when writing a message. A message will be sent to notify Users of the action, this message will be deleted after 5 minutes.

    Tags:
        polizei:
            exclude: Don't ban gbanned users
        grenschutz:
            silent: Don't send the notification message
            exclude: Don't ban gbanned users
    """
    if event.is_private:
        return

    if isinstance(event, ChatAction.Event):
        if event.user_left or event.user_kicked:
            return

    if isinstance(event, ChatAction.Event):
        if event.action_message is None:
            return
        elif not isinstance(event.action_message.action,
                            (MessageActionChatJoinedByLink, MessageActionChatAddUser)):
            return
    client: Client = event.client
    try:
        chat: Channel = await event.get_chat()
    except ChannelPrivateError:
        return
    if not chat.creator and not chat.admin_rights:
        return
    if chat.admin_rights:
        if not chat.admin_rights.ban_users:
            return
    db: Database = client.db
    tags = await Tags.from_event(event)
    polizei_tag = tags.get('polizei')
    grenzschutz_tag = tags.get('grenzschutz')
    silent = grenzschutz_tag == 'silent'
    if grenzschutz_tag == 'exclude' or polizei_tag == 'exclude':
        return

    if isinstance(event, ChatAction.Event):
        uid = event.user_id
    elif isinstance(event, NewMessage.Event):
        uid = event.message.from_id
    else:
        return
    if uid is None:
        return
    try:
        entity = await client.get_entity(uid)
        name = get_display_name(entity)
    except GET_ENTITY_ERRORS:
        name = uid

    result = await db.banlist.get(uid)
    if not result:
        return
    else:
        ban_reason = result.reason
    admins = [p.id for p in await client.get_participants(event.chat_id, filter=ChannelParticipantsAdmins())]
    if uid not in admins:
        try:
            await client.ban(chat, uid)
        except UserIdInvalidError as err:
            logger.error("Error occured while banning %s", err)
            return
        await event.delete()
        if not silent:
            message = KanTeXDocument(Section(
                Bold('SpamWatch Grenzschutz Ban'),
                KeyValueItem(Bold("User"),
                             f'{Mention(name, uid)} [{Code(uid)}]'),
                KeyValueItem(Bold("Reason"),
                             ban_reason)
            ))
            delete_time = '2m30s' if 'kriminalamt' not in ban_reason.lower() else '10s'
            await client.respond(event, str(message), reply=False, delete=delete_time)
