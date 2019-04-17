from typing import Optional

from telethon import TelegramClient

from database.arango import ArangoDB
from utils.pluginmgr import PluginManager


class KantekClient(TelegramClient):
    """Custom telethon client that has the plugin manager as attribute."""
    plugin_mgr: Optional[PluginManager] = None
    db: ArangoDB = None

    async def respond(self, event, msg, reply=True):
        if reply:
            await event.respond(msg, reply_to=(event.reply_to_msg_id or event.message.id))
        else:
            await event.respond(msg, reply_to=event.message.id)
