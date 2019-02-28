"""Main bot module. Setup logging, register components"""
import asyncio
import logging

from telethon import TelegramClient, events
import logzero
from telethon.events import NewMessage

import config
import components
from components import utils
from plugins import PluginManager

__version__ = '0.1.0'

def main():
    """Register logger and components."""

    log = logzero.setup_logger('kantek-logger', level=logging.INFO)
    tlog = logging.getLogger('kantek-channel-log')
    tlog.setLevel(logging.INFO)
    handler = utils.TGChannelLogHandler(config.log_bot_token,
                                        config.log_channel_id)
    formatter = utils.TGChannelFormatter('telethon')
    handler.setFormatter(formatter)
    tlog.addHandler(handler)

    client: TelegramClient = TelegramClient(config.session_name,
                                            config.api_id,
                                            config.api_hash)
    client.start(config.phone)

    log.info("Registering components")
    plugin_mgr = PluginManager()
    client.run_until_disconnected()


if __name__ == '__main__':
    main()
