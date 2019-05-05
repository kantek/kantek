"""Plugin to manage the autobahn"""
import logging
from typing import Dict, List

from telethon import events
from telethon.events import NewMessage
from telethon.tl.patched import Message
from telethon.tl.types import Channel, User

from config import cmd_prefix
from database.arango import ArangoDB
from utils import parsers
from utils.client import KantekClient
from utils.mdtex import Bold, Code, Item, KeyValueItem, MDTeXDocument, Section, SubSection

__version__ = '0.1.0'

tlog = logging.getLogger('kantek-channel-log')

AUTOBAHN_TYPES = {
    'bio': '0x0',
    'string': '0x1',
    'filename': '0x2',
    'channel': '0x3',
    'preemptive': '0x9'
}

@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}a(uto)?b(ahn)?'))
async def autobahn(event: NewMessage.Event) -> None:
    """Command to manage autobahn blacklists"""
    client: KantekClient = event.client
    msg: Message = event.message
    db: ArangoDB = client.db
    args = msg.raw_text.split()[1:]

    response = ''
    if not args:
        pass

    elif args[0] == 'add' and len(args) > 1:
        response = await _add_string(event, db)
    if response:
        await client.respond(event, response)


async def _add_string(event: NewMessage.Event, db: ArangoDB) -> MDTeXDocument:
    """Add a string to the Collection of its type"""
    msg: Message = event.message
    args = msg.raw_text.split()[2:]
    keyword_args, args = parsers.parse_arguments(' '.join(args))
    strings = [s.split(';', maxsplit=1) for s in args]
    added_items = []
    for item in strings:
        if len(item) != 2:
            continue
        string_type, string = item
        hex_type = AUTOBAHN_TYPES.get(string_type)
        collection = db.ab_collection_map.get(hex_type)
        if hex_type is None or collection is None:
            continue

        existing_one = collection.fetchByExample({'string': string}, batchSize=1)
        if not existing_one:
            collection.add_string(string)
            added_items.append(item)

    return await _format_items(added_items)


async def _format_items(items: List[List[str]]) -> MDTeXDocument:
    """Format a list of lists into nice sections"""
    formatted = {}
    for string_type, string in items:
        type_list = formatted.get(string_type)
        if type_list is not None:
            formatted[string_type].append(Code(string))
        else:
            formatted[string_type] = [Code(string)]
    sections = []
    for string_type, strings in formatted.items():
        sections.append(SubSection(Bold(string_type), *strings))

    return MDTeXDocument(Section(Bold('Blacklisted items'), *sections))


