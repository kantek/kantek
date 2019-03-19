"""Plugin to get information about a channel."""
import logging

from telethon import events
from telethon.events import NewMessage
from telethon.tl.types import Chat

from config import cmd_prefix

__version__ = '0.1.0'

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}info'))
async def info(event: NewMessage.Event) -> None:
    """Show the information about a group or channel.

    Args:
        event: The event of the command

    Returns: None

    """
    chat: Chat = event.chat

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
    info_msg += [f'**{k}:**\n  `{v}`' for k, v in _info.items() if v is not None]

    await event.respond('\n'.join(info_msg),
                        reply_to=(event.reply_to_msg_id or event.message.id))
    tlog.info(f'Ran `info` in `{chat.title}`')
