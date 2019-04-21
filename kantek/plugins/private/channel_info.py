"""Plugin to get information about a channel."""
import logging

from telethon import events
from telethon.events import NewMessage
from telethon.tl.types import Channel, User

from config import cmd_prefix
from utils.client import KantekClient

__version__ = '0.1.0'

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}info'))
async def info(event: NewMessage.Event) -> None:
    """Show information about a group or channel.

    Args:
        event: The event of the command

    Returns: None

    """
    chat: Channel = event.chat
    client: KantekClient = event.client
    if event.is_private:
        return
    _info = {
        'title': chat.title,
        'chat_id': event.chat_id,
        'access_hash': chat.access_hash,
        'creator': chat.creator,
        'broadcast': chat.broadcast,
        'megagroup': chat.megagroup,
        'min': chat.min,
        'username': chat.username,
        'verified': chat.verified,
        'version': chat.version,
    }
    info_msg = [f'info for {chat.title}:']
    info_msg += [f'  **{k}:**\n    `{v}`' for k, v in _info.items() if v is not None]
    info_msg.append(f'\nuser stats:')
    bot_accounts = 0
    total_users = 0
    deleted_accounts = 0
    user: User
    async for user in client.iter_participants(chat):
        total_users += 1
        if user.bot:
            bot_accounts += 1
        if user.deleted:
            deleted_accounts += 1
    _info = {
        'total_users': total_users,
        'bots': bot_accounts,
        'deleted_accounts': deleted_accounts
    }
    info_msg += [f'  **{k}:**\n    `{v}`' for k, v in _info.items() if v is not None]

    await client.respond(event, '\n'.join(info_msg))
    tlog.info('Ran `info` in `%s`', chat.title)
