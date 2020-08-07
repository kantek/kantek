import logging
from typing import Dict

from telethon.tl.types import Channel

from utils.constants import GET_ENTITY_ERRORS
from utils.mdtex import *
from utils.pluginmgr import k, Command
from utils.tags import Tags

tlog = logging.getLogger('kantek-channel-log')


@k.command('tag')
async def tag(chat: Channel, tags: Tags, event: Command) -> MDTeXDocument:
    """Add, query or remove tags from groups and channels.

    Tags are used by various plugins to alter their functionality in the specific chats.
    Check each plugins help to see which tags are accepted.
    To list the tags of the current chat simply specify no subcommands

    Examples:
        {cmd}
    """
    named_tags: Dict = tags.named_tags
    data = []
    data += [KeyValueItem(key, Code(value)) for key, value in named_tags.items()]
    if not data:
        data.append(Code('None'))
    return MDTeXDocument(
        Section(Item(f'Tags for {chat.title}[{Code(event.chat_id)}]:'),
                *data)
    )


async def _get_valid_ids(chats, client):
    failed = []
    ids = set()
    if chats:
        for c in chats:
            try:
                chat = await client.get_entity(c)
            except GET_ENTITY_ERRORS:
                failed.append(str(c))
                continue

            if isinstance(chat, Channel):
                ids.add(int(f'-100{chat.id}'))
            else:
                failed.append(str(c))
    return ids, failed


@tag.subcommand(delete=True)
async def add(args, kwargs, db, client, event: Command) -> None:
    """Add tags to the chat.

    Arguments:
        `chats`: Optional list of chat ids and usernames the tags should be set for
        `kwargs`: Key: Value pairs of the tags you want to set

    Examples:
        {cmd} -1001129887931 -strafanzeige polizei: exclude
        {cmd} -strafanzeige polizei: exclude
        {cmd} gban: verbose
    """
    if args:
        chats, failed = await _get_valid_ids(args, client)
    else:
        chats = {event.chat_id}
        failed = []

    for cid in chats:
        tags = await Tags.from_id(db, cid, private=False)
        for name, value in kwargs.items():
            await tags.set(name, value)

    if failed:
        tlog.warning(f'Could not set tags for {Code(", ".join(failed))}')


@tag.subcommand(delete=True)
async def del_(args, kwargs, db, client, event: Command) -> None:
    """Delete the specified tags from the chat.

    Arguments:
        `keys`: Tags to delete
        `chats`: List of chats the tags should be deleted from

    Examples:
        {cmd} chats: [-1001129887931] gban
        {cmd} gban polizei
        {cmd} network
    """

    if entities := kwargs.get('chats'):
        chats, failed = await _get_valid_ids(entities, client)
    else:
        chats = {event.chat_id}
        failed = []

    for cid in chats:
        tags = await Tags.from_id(db, cid, private=False)
        for arg in args:
            await tags.remove(arg)

    if failed:
        tlog.warning(f'Could not remove tags for {Code(", ".join(failed))}')


@tag.subcommand(delete=True)
async def clear(tags: Tags) -> None:
    """Clear all tags from the chat.

    Examples:
        {cmd}
    """
    await tags.clear()
