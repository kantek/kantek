"""Plugin to manage the autobahn"""
import logging

from telethon import events
from telethon.events import NewMessage

from config import cmd_prefix
from utils.client import KantekClient

__version__ = '0.1.0'

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}kill'))
async def kill(event: NewMessage.Event) -> None:
    """Plugin to kill the userbot incase something bad happens."""
    client: KantekClient = event.client
    tlog.info('.kill executed. Disconnecting.')
    await client.disconnect()
