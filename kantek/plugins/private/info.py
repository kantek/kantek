from typing import Dict, List

import telethon.utils
from kantex.md import *
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import Channel, ChannelParticipantsAdmins, ChannelParticipantCreator

from kantek import Client, Database, Config
from kantek import k, Command


@k.command('info')
async def info(client: Client, args: List, db: Database) -> KanTeXDocument:
    """"Get info about a chat

    Arguments:
        `chat`: Chat ID or Username

    Examples:
        {cmd} -1001129887931
    """

    chat = args[0]
    entity: Channel = await client.get_cached_entity(chat)
    if entity is not None:
        chat_id = telethon.utils.get_peer_id(entity)
        title = entity.title
        await db.chats.add(chat_id, title)
    else:
        chat = await db.chats.get(chat)
        if chat is None:
            return KanTeXDocument(Section('ValueError', 'chat not found'))
        chat_id = chat.id
        title = chat.title

    sections = [
        Section('Chat Info',
                KeyValueItem('chat_id', Code(chat_id)),
                KeyValueItem('title', Code(title))),
    ]

    if entity is not None:
        config = Config()
        items = []
        admins_ids = []
        async for p in client.iter_participants(entity, filter=ChannelParticipantsAdmins):
            participant = await client(GetParticipantRequest(entity, p))
            if isinstance(participant.participant, ChannelParticipantCreator):
                items.append(Code(f'{config.prefix}gban {p.id} "Spamadd[0x0 {chat_id}]"'))
            elif not p.bot:
                admins_ids.append(str(p.id))

        items.append(Code(f'{config.prefix}gban {" ".join(admins_ids)} "Spamadd[0x1 {chat_id}]"'))

        sections.append(Section('Admins', *items))
    # TODO Implement this
    # data = []
    # data += [KeyValueItem(key, Code(value)) for key, value in tags.named_tags.items()]
    # sections.append(Section('Tags:', *data or [Italic('None')]))

    return KanTeXDocument(*sections)
