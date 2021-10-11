import logging

from telethon.errors import ChatNotModifiedError
from telethon.tl.custom import Message
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.functions.messages import EditChatDefaultBannedRightsRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantCreator, ChannelParticipantAdmin

from kantek import Database
from kantek import Client
from kantex.md import *
from kantek import k, Command

tlog = logging.getLogger('kantek-channel-log')


@k.command('unlock', admins=True)
async def unlock(client: Client, db: Database, chat, event: Command, msg: Message) -> KanTeXDocument:
    """Restore a chats previous permissions

    Arguments:
        `-self`: Use to make other Kantek instances ignore your command

    Examples:
        {cmd}
    """
    participant = (await client(GetParticipantRequest(chat, msg.sender_id))).participant
    permitted = False
    if isinstance(participant, ChannelParticipantCreator):
        permitted = True
    elif isinstance(participant, ChannelParticipantAdmin):
        rights = participant.admin_rights
        permitted = rights.ban_users
    if not permitted:
        return KanTeXDocument('Insufficient permission.')
    dbchat = await db.chats.get(event.chat_id)
    permissions = chat.default_banned_rights.to_dict()
    del permissions['_']
    if dbchat.locked:
        new_rights = permissions.copy()

        for k, v in dbchat.permissions.items():
            new_rights[k] = v
        try:
            await client(EditChatDefaultBannedRightsRequest(
                chat,
                banned_rights=ChatBannedRights(**new_rights)))
        except ChatNotModifiedError:
            pass
        await db.chats.unlock(event.chat_id)
        return KanTeXDocument('Chat unlocked.')
    else:
        return KanTeXDocument('Chat not locked.')
