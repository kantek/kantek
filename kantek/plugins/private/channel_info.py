"""Plugin to get information about a channel."""
import logging

from telethon import events
from telethon.events import NewMessage
from telethon.tl.types import Channel, User

from config import cmd_prefix
from utils.client import KantekClient
from utils.mdtex import Section, Bold, KeyValueItem, Code

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
    info_msg = Section(f'info for {chat.title}:',
                       KeyValueItem(Bold('title'), Code(chat.title)),
                       KeyValueItem(Bold('chat_id'), Code(event.chat_id)),
                       KeyValueItem(Bold('access_hash'), Code(chat.access_hash)),
                       KeyValueItem(Bold('creator'), Code(chat.creator)),
                       KeyValueItem(Bold('broadcast'), Code(chat.broadcast)),
                       KeyValueItem(Bold('megagroup'), Code(chat.megagroup)),
                       KeyValueItem(Bold('min'), Code(chat.min)),
                       KeyValueItem(Bold('username'), Code(chat.username)),
                       KeyValueItem(Bold('verified'), Code(chat.verified)),
                       KeyValueItem(Bold('version'), Code(chat.version)),
                       )

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

    info_msg += Section('user stats:',
                        KeyValueItem(Bold('total_users'), Code(total_users)),
                        KeyValueItem(Bold('bots'), Code(bot_accounts)),
                        KeyValueItem(Bold('deleted_accounts'), Code(deleted_accounts)))

    await client.respond(event, info_msg)
    tlog.info('Ran `info` in `%s`', chat.title)
