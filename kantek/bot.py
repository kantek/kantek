"""Main bot module. Setup logging, register components"""
import logging
import os

import logzero

import config
from database.arango import ArangoDB
from utils.client import KantekClient
from utils.loghandler import TGChannelLogHandler
from utils.pluginmgr import PluginManager

logger = logzero.setup_logger('kantek-logger', level=logging.DEBUG)
telethon_logger = logzero.setup_logger('telethon', level=logging.INFO)
tlog = logging.getLogger('kantek-channel-log')
handler = TGChannelLogHandler(config.log_bot_token,
                              config.log_channel_id)
tlog.addHandler(handler)
tlog.setLevel(logging.INFO)

__version__ = '0.1.0'


def main() -> None:
    """Register logger and components."""
    client: KantekClient = KantekClient(
        os.path.abspath(config.session_name),
        config.api_id,
        config.api_hash)
    client.start(config.phone)
    tlog.info(f'Started kantek v{__version__}')
    client.plugin_mgr = PluginManager(client)
    client.db = ArangoDB()
    client.plugin_mgr.register_all()
    client.run_until_disconnected()


if __name__ == '__main__':
    main()
