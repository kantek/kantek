import logging
import subprocess

from utils.client import Client
from utils.config import Config
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.command('kill')
async def kill(client: Client) -> None:
    """Plugin to kill the userbot incase something bad happens.

    Examples:
        {cmd}
    """
    config = Config()
    tlog.info('.kill executed. Disconnecting.')

    if config.kill_command is not None:
        subprocess.call(config.kill_command)
    else:
        await client.disconnect()
