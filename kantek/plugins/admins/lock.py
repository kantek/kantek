"""Plugin to manage the autobahn"""
import logging

from telethon.errors import ChatNotModifiedError
from telethon.tl.custom import Message
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.functions.messages import EditChatDefaultBannedRightsRequest
from telethon.tl.types import ChatBannedRights, InputPeerChannel, ChannelParticipantAdmin

from utils.client import KantekClient
from utils.mdtex import MDTeXDocument
from utils.pluginmgr import k, Command

tlog = logging.getLogger('kantek-channel-log')


@k.command('lock', admins=True)
async def lock(client: KantekClient, event: Command) -> None:
    """Command to quickly lock a chat to readonly for normal users."""
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
        await client.respond(event, MDTeXDocument('Chat locked.'))
    except ChatNotModifiedError:
        await client.respond(event, MDTeXDocument('Chat already locked.'))
