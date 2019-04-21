"""Plugin to handle tagging of chats and channels."""
import logging
from typing import Dict, List

from telethon import events
from telethon.events import NewMessage
from telethon.tl.types import Chat, Message

from config import cmd_prefix
from database.arango import ArangoDB
from utils import parsers
from utils.client import KantekClient

__version__ = '0.1.0'

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}tag'))
async def tag(event: NewMessage.Event) -> None:
    """Add or remove tags from groups and channels.

    Args:
        event: The event of the command

    Returns: None

    """
    chat: Chat = event.chat
    client: KantekClient = event.client
    db: ArangoDB = client.db
    chat_document = client.db.groups.get_chat(event.chat_id)
    msg: Message = event.message
    args = msg.raw_text.split()[1:]
    indent = 4
    response = False
    if not args:
        db_named_tags: Dict = chat_document['named_tags'].getStore()
        db_tags: List = chat_document['tags']
        data = [f'Tags for **{chat.title}**[`{event.chat_id}`]:']
        if not db_tags and not db_named_tags:
            data.append(f'{" " * indent}__None__')
        else:
            for k, v in db_named_tags.items():
                data.append(f'{" " * indent}**{k}:** {", ".join(v)}')
            for _tag in db_tags:
                data.append(f'{" " * indent}{_tag}')
        response = '\n'.join(data)
    elif args[0] == 'add' and len(args) > 1:
        response = await _add_tags(event, db)
    elif args[0] == 'clear' and len(args):
        response = await _clear_tags(event, db)
    elif args[0] == 'del' and len(args) > 1:
        response = await _delete_tags(event, db)
    if response:
        await client.respond(event, response)
    tlog.info(f'Ran `tag` in `{chat.title}`. Response: {response}')


async def _add_tags(event: NewMessage.Event, db: ArangoDB):
    """Add tags to chat.

    Args:
        event: The event of the command
        db: The database object

    Returns: A string with the action taken.
    """
    msg: Message = event.message
    args = msg.raw_text.split()[2:]
    chat_document = db.groups[event.chat_id]
    db_named_tags: Dict = chat_document['named_tags'].getStore()
    db_tags: List = chat_document['tags']
    named_tags, tags = parsers.parse_tag_syntax(' '.join(args))
    for k, v in named_tags.items():
        db_named_tags[k] = v
    for _tag in tags:
        if _tag not in db_tags:
            db_tags.append(_tag)
    chat_document['named_tags'] = db_named_tags
    chat_document['tags'] = db_tags
    chat_document.save()
    new_named_tags = ', '.join([f'`{k}: {v}`' for k, v in named_tags.items() if v is not None])
    new_tags = ', '.join(tags)
    return f'Added {new_tags} {(", ".join(named_tags))}.'


async def _clear_tags(event: NewMessage.Event, db: ArangoDB):
    """Remove all tags from a chat.

    Args:
        event: The event of the command
        db: The database object

    Returns: A string with the action taken.
    """
    chat_document = db.groups[event.chat_id]
    chat_document['named_tags'] = {}
    chat_document['tags'] = []
    chat_document.save()
    return 'Cleared tags.'


async def _delete_tags(event: NewMessage.Event, db: ArangoDB):
    """Delete the specified tags from a chat.

    Args:
        event: The event of the command
        db: The database object

    Returns: A string with the action taken.
    """
    msg: Message = event.message
    args = msg.raw_text.split()[2:]
    chat_document = db.groups[event.chat_id]
    db_named_tags: Dict = chat_document['named_tags'].getStore()
    db_tags: List = chat_document['tags']
    for arg in args:
        if arg in db_named_tags:
            del db_named_tags[arg]
            db_named_tags = db_named_tags
        if arg in db_tags:
            del db_tags[db_tags.index(arg)]
    chat_document['named_tags'] = db_named_tags
    chat_document.save()
    return f'Deleted {", ".join(args)}.'
