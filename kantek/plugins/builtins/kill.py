import logging
import subprocess
import shlex

import logzero

from kantek import Client
from kantek import Config
from kantek.utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')
logger: logging.Logger = logzero.logger

@k.command('kill')
async def kill(client: Client) -> None:
    """Plugin to kill the userbot incase something bad happens.

    Examples:
        {cmd}
    """
    config = Config()
    tlog.info('.kill executed. Disconnecting.')

    if config.kill_command is not None:
        try:
            subprocess.call(shlex.split(config.kill_command))
        except FileNotFoundError as e:
            logger.exception(e)
            await client.disconnect()
    else:
        await client.disconnect()
