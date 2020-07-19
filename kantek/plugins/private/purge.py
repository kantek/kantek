"""Plugin to purge messages up to a specific point"""
import logging
from typing import Dict, List

from telethon.tl.custom import Message
from telethon.tl.types import Channel

from utils.client import KantekClient
from utils.pluginmgr import k, Command

tlog = logging.getLogger('kantek-channel-log')


@k.command('purge')
async def purge(client: KantekClient, chat: Channel, msg: Message,
                  args: List, kwargs: Dict, event: Command) -> None:
    """Plugin to purge messages up to a specific point."""
    await msg.delete()
    if not msg.is_reply:
        return
    else:
        reply_msg: Message = await msg.get_reply_message()
        await client.delete_messages(chat, list(range(reply_msg.id, msg.id)))
