from telethon.events import NewMessage
from telethon.tl.patched import Message

from kantek.utils.pluginmgr import k


@k.command('delete')
async def delete(event: NewMessage.Event) -> None:
    """Delete the message that was replied to"""
    msg: Message = event.message
    await msg.delete()
    if msg.is_reply:
        reply_msg: Message = await msg.get_reply_message()
        if reply_msg:
            await reply_msg.delete()
