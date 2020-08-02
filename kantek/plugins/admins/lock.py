import logging

from telethon.errors import ChatNotModifiedError
from telethon.tl.functions.messages import EditChatDefaultBannedRightsRequest
from telethon.tl.types import ChatBannedRights, Chat

from database.database import Database
from utils.client import Client
from utils.mdtex import *
from utils.pluginmgr import k, Command

tlog = logging.getLogger('kantek-channel-log')


@k.command('lock', admins=True)
async def lock(client: Client, db: Database, chat: Chat, event: Command) -> MDTeXDocument:
    """Set a chat to read only.

    Arguments:
        `-self`: Use to make other Kantek instances ignore your command

    Examples:
        {cmd}
    """
    permissions = chat.default_banned_rights.to_dict()
    del permissions['_']
    del permissions['until_date']
    del permissions['view_messages']
    await db.chats.lock(event.chat_id, {k: v for k, v in permissions.items() if not v})
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
