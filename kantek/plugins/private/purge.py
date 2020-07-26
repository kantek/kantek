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

    This command is unavailable in private for the moment since private message ids are shared across PMs

    Arguments:
        `count`: Delete `count` messages

    Examples:
        {cmd}
    """
    await msg.delete()
    if event.is_private:
        return
    if not msg.is_reply:
        if args:
            count = args[0]
            message_ids = [msg.id]
            async for m in client.iter_messages(chat, limit=count, offset_id=msg.id):
                message_ids.append(m.id)
            await client.delete_messages(chat, message_ids)
        else:
            return
    else:
        reply_msg: Message = await msg.get_reply_message()
        await client.delete_messages(chat, list(range(reply_msg.id, msg.id)))
