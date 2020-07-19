"""Plugin to get information about a channel."""
import logging

from telethon import events
from telethon.events import NewMessage

from utils.client import KantekClient
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.event(events.NewMessage())
async def add_groups(event: NewMessage.Event) -> None:
    """Show the information about a group or channel.

    Args:
        event: The event of the command

    Returns: None

    """
    if event.is_private:
        return
    client: KantekClient = event.client
    client.db.groups.get_chat(event.chat_id)
