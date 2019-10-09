"""Main bot module. Setup logging, register components"""
import logging
import os

import logzero
import spamwatch

import config
from database.arango import ArangoDB
from utils.client import KantekClient
from utils.loghandler import TGChannelLogHandler
from utils.pluginmgr import PluginManager

try:
    from config import spamwatch_host, spamwatch_token
except ImportError:
    spamwatch_host = ''
    spamwatch_token = ''

logger = logzero.setup_logger('kantek-logger', level=logging.DEBUG)
telethon_logger = logzero.setup_logger('telethon', level=logging.INFO)
tlog = logging.getLogger('kantek-channel-log')
handler = TGChannelLogHandler(config.log_bot_token,
                              config.log_channel_id)
tlog.addHandler(handler)
tlog.setLevel(logging.INFO)

__version__ = '0.3.1'


def main() -> None:
    """Register logger and components."""
    client = KantekClient(
        os.path.abspath(config.session_name),
        config.api_id,
        config.api_hash)
    client.start(config.phone)
    client.kantek_version = __version__
    client.plugin_mgr = PluginManager(client)
    logger.info('Connecting to Database')
    client.db = ArangoDB()
    client.plugin_mgr.register_all()
    tlog.info('Started kantek v%s', __version__)
    logger.info('Started kantek v%s', __version__)

    if spamwatch_host and spamwatch_token:
        client.sw = spamwatch.Client(spamwatch_token, host=spamwatch_host)

    client.run_until_disconnected()


if __name__ == '__main__':
    main()
