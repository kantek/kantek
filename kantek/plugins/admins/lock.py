"""Plugin to manage the autobahn"""
import logging

from telethon.errors import ChatNotModifiedError
from telethon.events import NewMessage
from telethon.tl.custom import Message
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.functions.messages import EditChatDefaultBannedRightsRequest
from telethon.tl.types import ChatBannedRights, InputPeerChannel, ChannelParticipantAdmin

from utils.client import KantekClient
from utils.mdtex import MDTeXDocument
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.command('lock')
async def lock(event: NewMessage.Event) -> None:
    """Command to quickly lock a chat to readonly for normal users."""
    client: KantekClient = event.client
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


@k.command('lock', False)
async def lock_group_admins(event: NewMessage.Event) -> None:
    """Check if the issuer of the command is group admin. Then execute the cleanup command."""
    if event.is_channel:
        msg: Message = event.message
        client: KantekClient = event.client
        uid = msg.from_id
        result = await client(GetParticipantRequest(event.chat_id, uid))
        if isinstance(result.participant, ChannelParticipantAdmin):
            await lock(event)
            tlog.info(f'lock executed by [{uid}](tg://user?id={uid}) in `{(await event.get_chat()).title}`')
