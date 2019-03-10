from typing import Optional

from telethon import TelegramClient

from utils.pluginmgr import PluginManager


class KantekClient(TelegramClient):
    """Custom telethon client that has the plugin manager as attribute."""
    plugin_mgr: Optional[PluginManager] = None
