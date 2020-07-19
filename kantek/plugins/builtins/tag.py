"""Plugin to handle tagging of chats and channels."""
import logging
from typing import Dict, List

from telethon.events import NewMessage
from telethon.tl.custom import Message
from telethon.tl.types import Chat, Message

from database.arango import ArangoDB
from utils import parsers
from utils.client import KantekClient
from utils.mdtex import Bold, Code, Item, KeyValueItem, Section
from utils.pluginmgr import k
from utils.tagmgr import TagManager

tlog = logging.getLogger('kantek-channel-log')


@k.command('tag')
async def tag(event: NewMessage.Event) -> None:
    """Add or remove tags from groups and channels.

    Args:
        event: The event of the command

    Returns: None

    """
    chat: Chat = event.chat
    client: KantekClient = event.client
    db: ArangoDB = client.db
    msg: Message = event.message
    tag_mgr = TagManager(event)
    args = msg.raw_text.split()[1:]
    response = ''
    if not args:
        named_tags: Dict = tag_mgr.named_tags
        tags: List = tag_mgr.tags
        data = []
        data += [KeyValueItem(Bold(key), value) for key, value in named_tags.items()]
        data += [Item(_tag) for _tag in tags]
        if not data:
            data.append(Code('None'))
        response = Section(Item(f'Tags for {Bold(chat.title)}[{Code(event.chat_id)}]:'),
                           *data)
    elif args[0] == 'add' and len(args) > 1:
        await _add_tags(event)
    elif args[0] == 'clear':
        tag_mgr.clear()
    elif args[0] == 'del' and len(args) > 1:
        await _delete_tags(event)
    if not response:
        await msg.delete()
    else:
        await client.respond(event, response)


async def _add_tags(event: NewMessage.Event):
    """Add tags to chat.

    Args:
        event: The event of the command

    Returns: A string with the action taken.
    """
    msg: Message = event.message
    args = msg.raw_text.split()[2:]
    tag_mgr = TagManager(event)
    named_tags, tags = parsers.parse_arguments(' '.join(args))
    for name, value in named_tags.items():
        tag_mgr[name] = value
    for _tag in tags:
        tag_mgr.set(_tag)


async def _delete_tags(event: NewMessage.Event):
    """Delete the specified tags from a chat.

    Args:
        event: The event of the command

    Returns: A string with the action taken.
    """
    msg: Message = event.message
    tag_mgr = TagManager(event)
    args = msg.raw_text.split()[2:]
    _, args = parsers.parse_arguments(' '.join(args))
    for arg in args:
        del tag_mgr[arg]
