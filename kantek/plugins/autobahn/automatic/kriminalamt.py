"""Plugin that automatically bans if a user joins and leaves immediately"""
import asyncio
import logging

import logzero
from telethon import events
from telethon.errors import UserNotParticipantError
from telethon.events import ChatAction
from telethon.tl.functions.channels import (DeleteUserHistoryRequest,
                                            GetParticipantRequest)
from telethon.tl.types import Channel, User

from utils.client import KantekClient
from utils.pluginmgr import k
from utils.tagmgr import TagManager

tlog = logging.getLogger('kantek-channel-log')
logger: logging.Logger = logzero.logger


@k.event(events.chataction.ChatAction(), name='kriminalamt')
async def kriminalamt(event: ChatAction.Event) -> None:
    """Ban a user when he joins and leaves in the configured interval"""
    client: KantekClient = event.client
    chat: Channel = await event.get_chat()
    user: User = await event.get_user()
    tags = TagManager(event)
    kriminalamt_tag = tags.get('kriminalamt')
    bancmd = tags.get('gbancmd', 'manual')
    delay = 1
    if not event.user_joined:
        return
    if not kriminalamt_tag or user.bot:
        return
    elif isinstance(kriminalamt_tag, int):
        delay = kriminalamt_tag
    elif isinstance(kriminalamt_tag, str) and kriminalamt_tag.isdigit():
        delay = int(kriminalamt_tag)
    await asyncio.sleep(delay)

    try:
        await client(GetParticipantRequest(chat, user))
    except UserNotParticipantError:
        reason = f'Kriminalamt #{chat.id} No. {delay}'
        userid = event.user_id
        await client.gban(userid, reason)

        if chat.creator or chat.admin_rights:
            if bancmd == 'manual':
                await client.ban(chat, userid)
            elif bancmd is not None:
                await event.reply(f'{bancmd} {userid} {reason}')
                await asyncio.sleep(0.25)

            messages = await client.get_messages(chat, from_user=userid, limit=0)
            if messages.total <= 5:
                await client(DeleteUserHistoryRequest(chat, userid))
            else:
                await event.delete()
