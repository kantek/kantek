"""Plugin to purge messages up to a specific point"""
import logging

from telethon.tl.custom import Message
from telethon.tl.types import Channel

from utils.client import Client
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.command('purge')
async def puge(client: Client, chat: Channel, msg: Message, args, event) -> None:
    """Purge all messages from the the point the command was sent to the message that was replied to.

    Arguments:
        `count`: Delete `count` messages

    Examples:
        {cmd}
    """
    await msg.delete()
    if not msg.is_reply:
        if args:
            count = args[0]
            message_ids = [msg.id]
            async for m in client.iter_messages(chat, limit=count, offset_id=msg.id):
                message_ids.append(m.id)
        else:
            return
    else:
        reply_msg: Message = await msg.get_reply_message()
        if event.is_private:
            message_ids = await client.get_messages(chat, min_id=reply_msg.id, max_id=msg.id)
        else:
            message_ids = list(range(reply_msg.id, msg.id))
    await client.delete_messages(chat, message_ids)
