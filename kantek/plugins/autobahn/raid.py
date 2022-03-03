import asyncio
from typing import Dict, List

from telethon.errors import FloodWaitError, UserNotParticipantError, BadRequestError
from telethon.tl.functions.channels import DeleteMessagesRequest, GetParticipantRequest
from telethon.tl.patched import Message
from telethon.tl.types import Channel, MessageActionChatAddUser, ChannelParticipantBanned

from kantek import Client, Database
from kantex.md import *
from kantek import k, Command
from kantek.utils.tags import Tags


@k.command('raid')
async def raid(event: Command, tags: Tags, db: Database) -> KanTeXDocument:
    """"Description

    Arguments:
        `arg`: Args

    Examples:
        {cmd} ...
    """
    pass



@raid.subcommand('start', delete=True)
async def start(chat: Channel, db: Database, msg: Message, args: List, event: Command):
    if msg.is_reply:
        reply_msg = await msg.get_reply_message()
        await db.chats.start_raid(event.chat_id, reply_msg.id)


@raid.subcommand('stop', delete=True)
async def stop(chat: Channel, client: Client, db: Database, event: Command, tags: Tags):
    db_chat = await db.chats.get(event.chat_id)
    start_id = db_chat.raid_start
    end_id = event.message.id
    await db.chats.stop_raid(event.chat_id)
    raidno = tags.get('raidno', None)

    user_ids = set()
    message_ids = set()
    async for msg in client.iter_messages(chat, min_id=start_id-1, reverse=True):
        if msg.id >= end_id + 1:
            break
        if isinstance(msg.action, MessageActionChatAddUser):
            action: MessageActionChatAddUser = msg.action
            if msg.sender_id in action.users:
                uid = msg.sender_id
                user_ids.add(uid)
                message_ids.add(msg.id)

    await client(DeleteMessagesRequest(chat, list(message_ids)))

    for uid in user_ids:
        try:
            result = await client(GetParticipantRequest(chat, uid))
            if not isinstance(result.participant, ChannelParticipantBanned):
                try:
                    await client.ban(chat, uid)
                except FloodWaitError as e:
                    flood_wait_message: Message = await client.send_message(chat, f'FloodWait for {e.seconds}')
                    await asyncio.sleep(e.seconds)
                    await flood_wait_message.delete()
                    await client.ban(chat, uid)
                    if raidno:
                        await client.gban(uid, f'Raid[{raidno}]')
            await asyncio.sleep(0.5)

        except (UserNotParticipantError, BadRequestError):
            pass

