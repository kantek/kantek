import logging
from datetime import timedelta

from telethon.errors import ChatNotModifiedError
from telethon.tl.custom import Message
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.functions.messages import EditChatDefaultBannedRightsRequest
from telethon.tl.types import ChatBannedRights, Chat, ChannelParticipantCreator, ChannelParticipantAdmin

from kantek import Database
from kantek.utils import parsers
from kantek import Client
from kantek import Config
from kantex.md import *
from kantek.utils.parsers import MissingExpression
from kantek import k, Command

tlog = logging.getLogger('kantek-channel-log')


@k.command('lock', admins=True)
async def lock(client: Client, db: Database, chat: Chat, event: Command, msg: Message, args) -> KanTeXDocument:
    """Set a chat to read only.

    Arguments:
        `duration`: How long the chat should be locked
        `-self`: Use to make other Kantek instances ignore your command

    Examples:
        {cmd} 2h
        {cmd} 1d
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

    duration = None
    if args:
        try:
            duration = parsers.time(args[0])
        except MissingExpression as err:
            return KanTeXDocument(Italic(err))

    if duration and duration < 10:
        return KanTeXDocument('Duration too short.')

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
        if duration:
            config = Config()
            await client.send_message(chat, f'{config.prefix}unlock', schedule=msg.date + timedelta(seconds=duration))
        return KanTeXDocument('Chat locked.')
    except ChatNotModifiedError:
        return KanTeXDocument('Chat already locked.')
