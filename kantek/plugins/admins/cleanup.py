import asyncio
import logging
from typing import Optional, Dict

import logzero
from telethon.errors import FloodWaitError, UserAdminInvalidError, MessageIdInvalidError
from telethon.tl.custom import Message
from telethon.tl.types import (Channel, User)

from utils.client import Client
from kantex.md import *
from utils.pluginmgr import k, Command

tlog = logging.getLogger('kantek-channel-log')
logger: logging.Logger = logzero.logger


@k.command('cleanup', admins=True)
async def cleanup(client: Client, chat: Channel, msg: Message,
                  kwargs: Dict, event: Command) -> None:
    """Remove or count all "Deleted Accounts" in a group.

    Arguments:
        `-count`: Only count deleted accounts and don't remove them
        `-silent`: Don't send a progress message
        `-self`: Use to make other Kantek instances ignore your command

    Examples:
        {cmd}
        {cmd} -count
        {cmd} -silent
    """
    count_only = kwargs.get('count', False)
    silent = kwargs.get('silent', False)
    waiting_message = None
    if silent:
        await msg.delete()
    else:
        waiting_message = await client.respond(event, 'Starting cleanup. This might take a while.')
    response = await _cleanup_chat(event, count=count_only, progress_message=waiting_message)
    if not silent:
        await client.respond(event, response, reply=False)
    if waiting_message:
        await waiting_message.delete()


async def _cleanup_chat(event, count: bool = False,
                        progress_message: Optional[Message] = None) -> KanTeXDocument:
    chat: Channel = await event.get_chat()
    client: Client = event.client
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
            progress = Section('Cleanup',
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
                        progress = Section('Cleanup | FloodWait',
                                           Bold(f'Got FloodWait for {error.seconds}s. Sleeping.'),
                                           KeyValueItem(Bold('Progress'),
                                                        f'{user_counter}/{participant_count}'),
                                           KeyValueItem(deleted_accounts_label, deleted_users))
                        await progress_message.edit(str(progress))

                    tlog.error(error)
                    logger.error(error)
                    await asyncio.sleep(error.seconds)
                    await client.ban(chat, user)

    return KanTeXDocument(
        Section('Cleanup',
                KeyValueItem(deleted_accounts_label, deleted_users),
                KeyValueItem(Bold('Deleted Admins'), deleted_admins) if deleted_admins else None))
