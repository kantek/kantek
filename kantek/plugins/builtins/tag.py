"""Plugin to handle tagging of chats and channels."""
import logging
from typing import Dict

from telethon.tl.types import Channel

from utils.mdtex import *
from utils.pluginmgr import k
from utils.tags import Tags

tlog = logging.getLogger('kantek-channel-log')


@k.command('tag')
async def tag(chat: Channel, tags: Tags) -> MDTeXDocument:
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
        Section(Item(f'Tags for {chat.title}[{Code(chat.id)}]:'),
                *data)
    )


@tag.subcommand()
async def add(args, kwargs, tags, event) -> None:
    """Add tags to the chat.
    Both positional and keyword argument are supported

    **Examples:**
        {cmd} -strafanzeige polizei: exclude
        {cmd} gban: verbose
    """
    for name, value in kwargs.items():
        await tags.set(name, value)
    await event.delete()


@tag.subcommand()
async def del_(args, tags, event) -> None:
    """Delete the specified tags from the chat.

    Arguments:
        `keys`: Tags to delete

    **Examples:**
        {cmd} gban polizei
        {cmd} network
    """
    for arg in args:
        await tags.remove(arg)
    await event.delete()


@tag.subcommand()
async def clear(tags: Tags, event) -> None:
    """Clear all tags from the chat.

    **Examples:**
        {cmd}
    """
    await tags.clear()
    await event.delete()
