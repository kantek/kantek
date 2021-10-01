import asyncio
import logging

import logzero
from telethon import events
from telethon.errors import UserNotParticipantError
from telethon.events import ChatAction
from telethon.tl.functions.channels import (DeleteUserHistoryRequest,
                                            GetParticipantRequest)
from telethon.tl.types import (Channel, User, ChannelAdminLogEventActionParticipantLeave,
                               ChannelAdminLogEventActionParticipantJoin)

from kantek import Client
from kantek.utils.constants import GET_ENTITY_ERRORS
from kantek.utils.pluginmgr import k
from kantek.utils.tags import Tags

tlog = logging.getLogger('kantek-channel-log')
logger: logging.Logger = logzero.logger


@k.event(events.chataction.ChatAction(), name='kriminalamt')
async def kriminalamt(event: ChatAction.Event) -> None:
    """Ban a user when they join and leave in the configured time.

    This plugin was made for a specific kind of bot that joins a chat, checks if the "Add Users" permission is enabled and if it is not it immediately leaves.

    The plugin is disabled by default and must first be enabled by setting the tag to True in a chat.

    Tags:
        `-kriminalamt`: If kriminalamt should run or not
    """
    client: Client = event.client
    chat: Channel = await event.get_chat()
    user: User = await event.get_user()
    tags = await Tags.from_event(event)
    enabled = tags.get('kriminalamt', False)
    bancmd = tags.get('gbancmd', 'manual')
    delay = 1
    if not event.user_joined or not (chat.creator or chat.admin_rights):
        return

    if not enabled or user.bot:
        return

    await asyncio.sleep(delay)

    try:
        await client(GetParticipantRequest(chat, user))
    except GET_ENTITY_ERRORS:
        return
    except UserNotParticipantError:
        userid = event.user.id
        leave_event = None
        async for e in client.iter_admin_log(chat, join=True, leave=True):
            if e.user_id == userid:
                if isinstance(e.action, ChannelAdminLogEventActionParticipantLeave):
                    leave_event = e
                elif isinstance(e.action, ChannelAdminLogEventActionParticipantJoin):
                    if leave_event and e.date < leave_event.date:
                        diff = leave_event.date - e.date
                        if diff.seconds > delay:
                            return
        if leave_event is None:
            return
        reason = f'Kriminalamt #{chat.id} No. {delay}'
        await client.gban(userid, reason)
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
