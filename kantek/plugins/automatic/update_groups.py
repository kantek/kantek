"""Plugin to get information about a channel."""
import logging

from telethon import events
from telethon.events import NewMessage
from telethon.tl.types import Channel, Chat

from config import cmd_prefix
from utils.client import KantekClient

__version__ = '0.1.0'

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage())
async def add_groups(event: NewMessage.Event) -> None:
    """Show the information about a group or channel.

    Args:
        event: The event of the command

    Returns: None

    """
    chat: Chat = event.chat

    if event.is_private:
        return
    client: KantekClient = event.client
    client.db.groups.add_chat(chat)
