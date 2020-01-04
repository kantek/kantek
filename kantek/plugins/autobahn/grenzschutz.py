"""Plugin to manage the autobahn"""
import logging
from typing import Dict, Union

import logzero
from telethon import events
from telethon.errors import UserIdInvalidError
from telethon.events import ChatAction, NewMessage
from telethon.tl.types import Channel

from database.arango import ArangoDB
from utils.client import KantekClient
from utils.mdtex import Bold, Code, KeyValueItem, MDTeXDocument, Mention, Section

__version__ = '0.1.1'

tlog = logging.getLogger('kantek-channel-log')
logger: logging.Logger = logzero.logger


@events.register(events.chataction.ChatAction())
@events.register(events.NewMessage())
async def grenzschutz(event: Union[ChatAction.Event, NewMessage.Event]) -> None:
    """Plugin to ban blacklisted users."""
    if event.is_private:
        return
    client: KantekClient = event.client
    chat: Channel = await event.get_chat()
    if not chat.creator and not chat.admin_rights:
        return
    if chat.admin_rights:
        if not chat.admin_rights.ban_users:
            return
    db: ArangoDB = client.db
    chat_document = db.groups.get_chat(event.chat_id)
    db_named_tags: Dict = chat_document['named_tags'].getStore()
    polizei_tag = db_named_tags.get('polizei')
    grenzschutz_tag = db_named_tags.get('grenzschutz')
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
        user = await client.get_entity(uid)
    except ValueError as err:
        logger.error(err)

    result = db.query('For doc in BanList '
                      'FILTER doc._key == @id '
                      'RETURN doc', bind_vars={'id': str(uid)})
    if not result:
        return
    else:
        ban_reason = result[0]['reason']
    try:
        await client.ban(chat, uid)
    except UserIdInvalidError as err:
        logger.error(f"Error occured while banning {err}")
        return

    if not silent:
        message = MDTeXDocument(Section(
            Bold('SpamWatch Grenzschutz Ban'),
            KeyValueItem(Bold("User"),
                         f'{Mention(user.first_name, uid)} [{Code(uid)}]'),
            KeyValueItem(Bold("Reason"),
                         ban_reason)
        ))
        await client.send_message(chat, str(message))
