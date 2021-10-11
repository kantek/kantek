from typing import Dict

from telethon.tl.functions.channels import DeleteUserHistoryRequest
from telethon.tl.patched import Message
from telethon.tl.types import Chat

from kantek import Client
from kantek import k


@k.command('ban', delete=True)
async def ban(client: Client, chat: Chat, msg: Message, kwargs: Dict) -> None:
    """"Ban user

    Arguments:
        `del`: Delete users messages if true

    Examples:
        {cmd}
        {cmd} -del
    """
    delall = kwargs.get('del')

    reply_msg: Message = await msg.get_reply_message()
    if reply_msg:
        await client.ban(chat, reply_msg.sender_id)
        if delall:
            await client(DeleteUserHistoryRequest(chat, reply_msg.sender_id))


