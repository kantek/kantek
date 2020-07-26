"""Plugin to manage the autobahn"""
import logging

from utils.client import Client
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.command('kill')
async def kill(client: Client) -> None:
    """Plugin to kill the userbot incase something bad happens.

    Examples:
        {cmd}
    """
    tlog.info('.kill executed. Disconnecting.')
    await client.disconnect()
