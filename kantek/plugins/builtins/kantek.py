"""Plugin to get information about kantek."""
import logging
import platform

import telethon
from telethon import events
from telethon.events import NewMessage

from config import cmd_prefix
from utils.client import KantekClient
from utils.mdtex import MDTeXDocument, Section, Bold, KeyValueItem

__version__ = '0.3.0'

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}kantek'))
async def tag(event: NewMessage.Event) -> None:
    """Show information about kantek.

    Args:
        event: The event of the command

    Returns: None

    """
    client: KantekClient = event.client

    await client.respond(event, MDTeXDocument(
        Section(f"{Bold('kantek')} userbot",
                KeyValueItem(Bold('source'), 'src.kv2.dev'),
                KeyValueItem(Bold('version'), client.kantek_version),
                KeyValueItem(Bold('telethon version'), telethon.__version__),
                KeyValueItem(Bold('python version'), platform.python_version()),
                KeyValueItem(Bold('plugins loaded'), len(client.plugin_mgr.active_plugins)))))
