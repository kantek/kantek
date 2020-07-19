"""Plugin to get information about kantek."""
import logging
from typing import List, Dict

from telethon.tl.types import Channel, Message

from utils.client import KantekClient
from utils.pluginmgr import k, Command

tlog = logging.getLogger('kantek-channel-log')


@k.command('test')
async def test(client: KantekClient, chat: Channel, msg: Message,
               args: List, kwargs: Dict, event: Command) -> None:
    """Show information about kantek.

    Args:
        event: The event of the command

    Returns: None

    """
    await msg.delete()
