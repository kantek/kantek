"""Plugin to manage the autobahn"""
import logging

from telethon.errors import ChatNotModifiedError
from telethon.tl.functions.messages import EditChatDefaultBannedRightsRequest
from telethon.tl.types import ChatBannedRights, InputPeerChannel

from utils.client import Client
from utils.mdtex import *
from utils.pluginmgr import k, Command

tlog = logging.getLogger('kantek-channel-log')


@k.command('lock', admins=True)
async def lock(client: Client, event: Command) -> MDTeXDocument:
    """Set a chat to read only.

    Examples:
        {cmd}
    """
    chat: InputPeerChannel = await event.get_input_chat()
    try:
        await client(EditChatDefaultBannedRightsRequest(
            chat,
            banned_rights=ChatBannedRights(
                until_date=None,
                view_messages=None,
                send_messages=True,
                send_media=True,
                send_stickers=True,
                send_gifs=True,
                send_games=True,
                send_inline=True,
                send_polls=True,
                change_info=True,
                invite_users=True,
                pin_messages=True
            )))
        return MDTeXDocument('Chat locked.')
    except ChatNotModifiedError:
        return MDTeXDocument('Chat already locked.')
