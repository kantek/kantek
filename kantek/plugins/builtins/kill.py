"""Plugin to manage the autobahn"""
import logging

from utils.client import KantekClient
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.command('kill')
async def kill(client: KantekClient) -> None:
    """Plugin to kill the userbot incase something bad happens.

    Examples:
        {cmd}
    """
    tlog.info('.kill executed. Disconnecting.')
    await client.disconnect()
