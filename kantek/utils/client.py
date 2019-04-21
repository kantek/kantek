"""File containing the Custom TelegramClient"""
from typing import Optional

from telethon import TelegramClient
from telethon.events import NewMessage

from database.arango import ArangoDB
from utils.pluginmgr import PluginManager


class KantekClient(TelegramClient):  # pylint: disable = R0901, W0223
    """Custom telethon client that has the plugin manager as attribute."""
    plugin_mgr: Optional[PluginManager] = None
    db: Optional[ArangoDB] = None
    kantek_version: str = ''

    async def respond(self, event: NewMessage.Event, msg: str, reply: bool = True) -> None:
        """Respond to the message an event caused or to the message that was replied to

        Args:
            event: The event of the message
            msg: The message text
            reply: If it should reply to the message that was replied to

        Returns: None

        """
        if reply:
            await event.respond(msg, reply_to=(event.reply_to_msg_id or event.message.id))
        else:
            await event.respond(msg, reply_to=event.message.id)
