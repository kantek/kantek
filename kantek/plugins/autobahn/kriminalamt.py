"""Plugin that automatically bans if a user joins and leaves immediately"""
import asyncio
import logging
from typing import Dict

import logzero
from telethon import events
from telethon.errors import UserNotParticipantError
from telethon.events import ChatAction
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import Channel

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
    delay = 1
    if not kriminalamt_tag:
        return
    elif kriminalamt_tag.isdigit():
        delay = int(kriminalamt_tag)
    await asyncio.sleep(delay)

    try:
        await client(GetParticipantRequest(chat, await event.get_input_user()))
    except UserNotParticipantError:
        await client.gban(event.user_id, f'Kriminalamt #{chat.id} No. {delay}')
