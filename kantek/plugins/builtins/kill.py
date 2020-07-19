"""Plugin to manage the autobahn"""
import logging

from telethon.events import NewMessage

from utils.client import KantekClient

__version__ = '0.1.0'

from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.command('kill')
async def kill(event: NewMessage.Event) -> None:
    """Plugin to kill the userbot incase something bad happens."""
    client: KantekClient = event.client
    tlog.info('.kill executed. Disconnecting.')
    await client.disconnect()
