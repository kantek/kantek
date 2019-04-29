"""Plugin to remove deleted Accounts from a group"""
import asyncio
import datetime
import logging
from typing import Optional

import logzero
from telethon import events
from telethon.errors import FloodWaitError, UserAdminInvalidError
from telethon.events import NewMessage
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.patched import Message
from telethon.tl.types import Channel, ChatBannedRights, User

from config import cmd_prefix
from utils import helpers
from utils.client import KantekClient
from utils.mdtex import Bold, KeyValueItem, MDTeXDocument, Section

__version__ = '0.2.0'

tlog = logging.getLogger('kantek-channel-log')
logger: logging.Logger = logzero.logger


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}cleanup'))
async def cleanup(event: NewMessage.Event) -> None:
    """Command to remove Deleted Accounts from a group or network."""
    chat: Channel = event.chat
    client: KantekClient = event.client
    keyword_args, args = await helpers.get_args(event)
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


async def _cleanup_chat(event, count: bool = False,
                        progress_message: Optional[Message] = None) -> MDTeXDocument:
    chat: Channel = event.chat
    client: KantekClient = event.client
    user: User
    deleted_users = 0
    deleted_admins = 0
    user_counter = 0
    participant_count = (await client.get_participants(chat, limit=0)).total
    modulus = participant_count // 25
    async for user in client.iter_participants(chat):
        if progress_message is not None and user_counter % modulus == 0:
            progress = Section(Bold('Cleanup'),
                               KeyValueItem(Bold('Progress'),
                                            f'{user_counter}/{participant_count}'),
                               KeyValueItem(Bold('Deleted Accounts'), deleted_users))
            await progress_message.edit(str(progress))
        user_counter += 1
        if user.deleted:
            deleted_users += 1
            if not count:
                try:
                    await client(EditBannedRequest(
                        chat, user, ChatBannedRights(
                            until_date=datetime.datetime(2038, 1, 1),
                            view_messages=True
                        )
                    ))
                except UserAdminInvalidError:
                    deleted_admins += 1
                except FloodWaitError as error:
                    if progress_message is not None:
                        progress = Section(Bold('Cleanup | FloodWait'),
                                           Bold(f'Got FloodWait for {error.seconds}s. Sleeping.'),
                                           KeyValueItem(Bold('Progress'),
                                                        f'{user_counter}/{participant_count}'),
                                           KeyValueItem(Bold('Deleted Accounts'), deleted_users))
                        await progress_message.edit(str(progress))

                    tlog.error(error)
                    logger.error(error)
                    await asyncio.sleep(error.seconds)
                    await client(EditBannedRequest(
                        chat, user, ChatBannedRights(
                            until_date=datetime.datetime(2038, 1, 1),
                            view_messages=True
                        )
                    ))

    return MDTeXDocument(
        Section(Bold('Cleanup'),
                KeyValueItem(Bold('Deleted Users'), deleted_users),
                KeyValueItem(Bold('Deleted Admins'), deleted_admins) if deleted_admins else None))
