from typing import Dict

from telethon.tl.patched import Message
from telethon.tl.types import Chat

from kantek import Client
from kantek import k


@k.command('kick', delete=True)
async def kick(client: Client, chat: Chat, msg: Message) -> None:
    """"Kick user

    Examples:
        {cmd}
    """
    reply_msg: Message = await msg.get_reply_message()
    if reply_msg:
        await client.kick_participant(chat, reply_msg.sender_id)

