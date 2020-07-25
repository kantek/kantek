"""Plugin to handle tagging of chats and channels."""
import logging
from typing import Dict, List

from telethon.tl.types import Channel

from utils.mdtex import *
from utils.pluginmgr import k
from utils.tagmgr import TagManager

tlog = logging.getLogger('kantek-channel-log')


@k.command('tag')
async def tag(chat: Channel, tags: TagManager) -> MDTeXDocument:
    """Add or remove tags from groups and channels.

    Args:
        event: The event of the command

    Returns: None

    """
    named_tags: Dict = tags.named_tags
    tags: List = tags.tags
    data = []
    data += [KeyValueItem(Bold(key), value) for key, value in named_tags.items()]
    data += [Item(_tag) for _tag in tags]
    if not data:
        data.append(Code('None'))
    return MDTeXDocument(
        Section(Item(f'Tags for {Bold(chat.title)}[{Code(chat.id)}]:'),
                *data)
    )


@tag.subcommand('add')
async def add(args, kwargs, tags, event) -> None:
    """Add tags to chat.

    Args:
        event: The event of the command

    Returns: A string with the action taken.
    """
    for name, value in kwargs.items():
        tags[name] = value
    for _tag in args:
        tags.set(_tag)
    await event.delete()


@tag.subcommand('del')
async def delete(args, tags, event) -> None:
    """Delete the specified tags from a chat.

    Args:
        event: The event of the command

    Returns: A string with the action taken.
    """
    for arg in args:
        del tags[arg]
    await event.delete()


@tag.subcommand('clear')
async def clear(tags: TagManager, event) -> None:
    tags.clear()
    await event.delete()
