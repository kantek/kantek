"""Plugin to remove deleted Accounts from a group"""
import asyncio
import logging
from typing import Optional

import logzero
from telethon.errors import FloodWaitError, UserAdminInvalidError, MessageIdInvalidError
from telethon.events import NewMessage
from telethon.tl.custom import Message
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import (Channel, User, ChannelParticipantAdmin)

from utils import helpers
from utils.client import KantekClient
from utils.mdtex import Bold, KeyValueItem, MDTeXDocument, Section
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')
logger: logging.Logger = logzero.logger


@k.command('cleanup')
async def cleanup(event: NewMessage.Event) -> None:
    """Command to remove Deleted Accounts from a group or network."""
    chat: Channel = await event.get_chat()
    client: KantekClient = event.client
    keyword_args, _ = await helpers.get_args(event)
    count_only = keyword_args.get('count', False)
    silent = keyword_args.get('silent', False)
    if not chat.creator and not chat.admin_rights:
        count_only = True
    waiting_message = None
    if silent:
        await event.message.delete()
    else:
        waiting_message = await client.respond(event, 'Starting cleanup. This might take a while.')
    response = await _cleanup_chat(event, count=count_only, progress_message=waiting_message)
    if not silent:
        await client.respond(event, response, reply=False)
    if waiting_message:
        await waiting_message.delete()


@k.command('cleanup', private=False)
async def cleanup_group_admins(event: NewMessage.Event) -> None:
    """Check if the issuer of the command is group admin. Then execute the cleanup command."""
    if event.is_channel:
        msg: Message = event.message
        client: KantekClient = event.client
        uid = msg.from_id
        result = await client(GetParticipantRequest(event.chat_id, uid))
        if isinstance(result.participant, ChannelParticipantAdmin):
            await cleanup(event)
            tlog.info(f'cleanup executed by [{uid}](tg://user?id={uid}) in `{(await event.get_chat()).title}`')


async def _cleanup_chat(event, count: bool = False,
                        progress_message: Optional[Message] = None) -> MDTeXDocument:
    chat: Channel = await event.get_chat()
    client: KantekClient = event.client
    user: User
    deleted_users = 0
    deleted_admins = 0
    user_counter = 0
    deleted_accounts_label = Bold('Counted Deleted Accounts' if count else 'Removed Deleted Accounts')
    participant_count = (await client.get_participants(chat, limit=0)).total
    # the number will be 0 if the group has less than 25 participants
    modulus = (participant_count // 25) or 1
    async for user in client.iter_participants(chat):
        if progress_message is not None and user_counter % modulus == 0:
            progress = Section(Bold('Cleanup'),
                               KeyValueItem(Bold('Progress'),
                                            f'{user_counter}/{participant_count}'),
                               KeyValueItem(deleted_accounts_label, deleted_users))
            try:
                await progress_message.edit(str(progress))
            except MessageIdInvalidError:
                progress_message = None
        user_counter += 1
        if user.deleted:
            deleted_users += 1
            if not count:
                try:
                    await client.ban(chat, user)
                except UserAdminInvalidError:
                    deleted_admins += 1
                except FloodWaitError as error:
                    if progress_message is not None:
                        progress = Section(Bold('Cleanup | FloodWait'),
                                           Bold(f'Got FloodWait for {error.seconds}s. Sleeping.'),
                                           KeyValueItem(Bold('Progress'),
                                                        f'{user_counter}/{participant_count}'),
                                           KeyValueItem(deleted_accounts_label, deleted_users))
                        await progress_message.edit(str(progress))

                    tlog.error(error)
                    logger.error(error)
                    await asyncio.sleep(error.seconds)
                    await client.ban(chat, user)

    return MDTeXDocument(
        Section(Bold('Cleanup'),
                KeyValueItem(deleted_accounts_label, deleted_users),
                KeyValueItem(Bold('Deleted Admins'), deleted_admins) if deleted_admins else None))
