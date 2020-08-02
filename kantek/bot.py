"""Main bot module. Setup logging, register components"""
import asyncio
import logging

import logzero
from spamwatch.client import Client as SWClient

from database.database import Database
from utils import helpers
from utils.client import Client
from utils.config import Config
from utils.loghandler import TGChannelLogHandler
from utils.pluginmgr import PluginManager

logger = logzero.setup_logger('kantek-logger', level=logging.DEBUG)
telethon_logger = logzero.setup_logger('telethon', level=logging.INFO)
tlog = logging.getLogger('kantek-channel-log')

tlog.setLevel(logging.INFO)

__version__ = '0.3.1'


async def main() -> None:
    """Register logger and components."""
    config = Config()

    handler = TGChannelLogHandler(config.log_bot_token,
                                  config.log_channel_id)
    await handler.connect()
    tlog.addHandler(handler)
    client = Client(str(config.session_name), config.api_id, config.api_hash)
    # noinspection PyTypeChecker
    await client.start(config.phone)
    client.config = config
    client.kantek_version = __version__

    client.plugin_mgr = PluginManager(client)
    client.plugin_mgr.register_all()

    logger.info('Connecting to Database')
    client.db = Database()
    await client.db.connect(config)

    tlog.info('Started Kantek v%s [%s]', __version__, helpers.link_commit(helpers.get_commit()))
    logger.info('Started Kantek v%s', __version__)

    if config.spamwatch_host and config.spamwatch_token:
        client.sw = SWClient(config.spamwatch_token, host=config.spamwatch_host)
        client.sw_url = config.spamwatch_host

    await client.run_until_disconnected()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
