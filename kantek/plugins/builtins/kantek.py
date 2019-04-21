"""Plugin to get information about kantek."""
import logging
import platform

from telethon import events
from telethon.events import NewMessage
from telethon.tl.types import Chat

from config import cmd_prefix
from utils.client import KantekClient

__version__ = '0.1.0'

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}kantek'))
async def tag(event: NewMessage.Event) -> None:
    """Show the information about kantek.

    Args:
        event: The event of the command

    Returns: None

    """
    chat: Chat = event.chat
    client: KantekClient = event.client
    response = ['**kantek** userbot']
    _info = {
        'version': client.kantek_version,
        'telethon version': client.__version__,
        'python version': platform.python_version(),
        'plugins loaded': len(client.plugin_mgr.active_plugins)
    }

    response += [f'  **{k}:**\n    `{v}`' for k, v in _info.items() if v is not None]
    await client.respond(event, '\n'.join(response))
    tlog.info('Ran `kantek` in `%s`', chat.title)
