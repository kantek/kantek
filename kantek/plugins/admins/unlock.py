import logging

from telethon.tl.functions.messages import EditChatDefaultBannedRightsRequest
from telethon.tl.types import ChatBannedRights

from database.database import Database
from utils.client import Client
from utils.mdtex import *
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.command('unlock', admins=True)
async def unlock(client: Client, db: Database, chat) -> MDTeXDocument:
    """Restore a chats previous permissions

    Arguments:
        `-self`: Use to make other Kantek instances ignore your command

    Examples:
        {cmd}
    """
    dbchat = await db.chats.get(chat.id)
    permissions = chat.default_banned_rights.to_dict()
    del permissions['_']
    if dbchat.locked:
        new_rights = permissions.copy()

        for k, v in dbchat.permissions.items():
            new_rights[k] = v

        await client(EditChatDefaultBannedRightsRequest(
            chat,
            banned_rights=ChatBannedRights(**new_rights)))
        await db.chats.unlock(chat.id)
        return MDTeXDocument('Chat unlocked.')
    else:
        return MDTeXDocument('Chat not locked.')
