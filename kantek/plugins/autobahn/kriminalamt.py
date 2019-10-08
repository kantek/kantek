"""Plugin that automatically bans if a user joins and leaves immediately"""
import asyncio
import datetime
import logging
from typing import Dict

import logzero
from telethon import events
from telethon.errors import UserNotParticipantError
from telethon.events import ChatAction
from telethon.tl.functions.channels import (DeleteUserHistoryRequest,
                                            EditBannedRequest,
                                            GetParticipantRequest)
from telethon.tl.types import Channel, ChatBannedRights

from database.arango import ArangoDB
from utils.client import KantekClient

__version__ = '0.1.0'

tlog = logging.getLogger('kantek-channel-log')
logger: logging.Logger = logzero.logger


@events.register(events.ChatAction())
async def kriminalamt(event: ChatAction.Event) -> None:
    client: KantekClient = event.client
    chat: Channel = await event.get_chat()
    db: ArangoDB = client.db
    chat_document = db.groups.get_chat(event.chat_id)
    db_named_tags: Dict = chat_document['named_tags'].getStore()
    kriminalamt_tag = db_named_tags.get('kriminalamt')
    bancmd = db_named_tags.get('gbancmd', 'manual')
    delay = 1
    if not kriminalamt_tag:
        return
    elif isinstance(kriminalamt_tag, int):
        delay = kriminalamt_tag
    elif isinstance(kriminalamt_tag, str) and kriminalamt_tag.isdigit():
        delay = int(kriminalamt_tag)
    await asyncio.sleep(delay)

    try:
        await client(GetParticipantRequest(chat, await event.get_input_user()))
    except UserNotParticipantError:
        reason = f'Kriminalamt #{chat.id} No. {delay}'
        userid = event.user_id
        await client.gban(userid, reason)

        if chat.creator or chat.admin_rights:
            if bancmd == 'manual':
                await client(EditBannedRequest(
                    chat, userid, ChatBannedRights(
                        until_date=datetime.datetime(2038, 1, 1),
                        view_messages=True
                    )
                ))
            elif bancmd is not None:
                await event.reply(f'{bancmd} {userid} {reason}')
                await asyncio.sleep(0.25)

            messages = await client.get_messages(chat, from_user=userid, limit=0)
            if messages.total <= 5:
                await client(DeleteUserHistoryRequest(chat, userid))
            else:
                await event.delete()
