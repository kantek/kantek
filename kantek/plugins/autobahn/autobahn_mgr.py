"""Plugin to manage the autobahn"""
import logging
import re
from urllib import parse

import requests
from pyArango.document import Document
from requests import ConnectionError
from telethon import events
from telethon.events import NewMessage
from telethon.tl.patched import Message

from config import cmd_prefix
from database.arango import ArangoDB
from utils import helpers, parsers, constants
from utils.client import KantekClient
from utils.mdtex import Bold, Code, KeyValueItem, MDTeXDocument, Pre, Section, SubSection

__version__ = '0.2.1'

tlog = logging.getLogger('kantek-channel-log')

AUTOBAHN_TYPES = {
    'bio': '0x0',
    'string': '0x1',
    'filename': '0x2',
    'channel': '0x3',
    'domain': '0x4',
    'preemptive': '0x9'
}

INVITELINK_PATTERN = re.compile(r'(?:joinchat|join)(?:/|\?invite=)(.*|)')


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
    elif args[0] == 'del' and len(args) > 1:
        response = await _del_string(event, db)
    elif args[0] == 'query' and len(args) > 1:
        response = await _query_string(event, db)
    if response:
        await client.respond(event, response)


async def _add_string(event: NewMessage.Event, db: ArangoDB) -> MDTeXDocument:
    """Add a string to the Collection of its type"""
    msg: Message = event.message
    args = msg.raw_text.split()[2:]
    _, args = parsers.parse_arguments(' '.join(args))
    string_type = args[0]
    strings = args[1:]
    added_items = []
    existing_items = []
    skipped_items = []
    for string in strings:
        hex_type = AUTOBAHN_TYPES.get(string_type)
        collection = db.ab_collection_map.get(hex_type)
        if hex_type is None or collection is None:
            continue
        if hex_type == '0x3':
            link_creator, chat_id, random_part = await helpers.resolve_invite_link(string)
            string = chat_id
        elif hex_type == '0x4':
            string = await helpers.resolve_url(string)
            if string in constants.TELEGRAM_DOMAINS:
                skipped_items.append(string)
                continue

        existing_one = collection.fetchByExample({'string': string}, batchSize=1)

        if not existing_one:
            collection.add_string(string)
            added_items.append(Code(string))
        else:
            existing_items.append(Code(string))

    return MDTeXDocument(Section(Bold('Added Items:'),
                                 SubSection(Bold(string_type),
                                            *added_items)) if added_items else '',
                         Section(Bold('Existing Items:'),
                                 SubSection(Bold(string_type),
                                            *existing_items)) if existing_items else '',
                         Section(Bold('Skipped Items:'),
                                 SubSection(Bold(string_type),
                                            *skipped_items)) if skipped_items else '',
                         )


async def _del_string(event: NewMessage.Event, db: ArangoDB) -> MDTeXDocument:
    """Add a string to the Collection of its type"""
    msg: Message = event.message
    args = msg.raw_text.split()[2:]
    _, args = parsers.parse_arguments(' '.join(args))
    string_type = args[0]
    strings = args[1:]
    removed_items = []
    for string in strings:
        hex_type = AUTOBAHN_TYPES.get(string_type)
        collection = db.ab_collection_map.get(hex_type)
        if hex_type is None or collection is None:
            continue

        if hex_type == '0x3':
            link_creator, chat_id, random_part = await helpers.resolve_invite_link(string)
            string = chat_id

        existing_one: Document = collection.fetchFirstExample({'string': string})
        if existing_one:
            existing_one[0].delete()
            removed_items.append(string)

    return MDTeXDocument(Section(Bold('Deleted Items:'),
                                 SubSection(Bold(string_type),
                                            *removed_items)))


async def _query_string(event: NewMessage.Event, db: ArangoDB) -> MDTeXDocument:
    """Add a string to the Collection of its type"""
    msg: Message = event.message
    args = msg.raw_text.split()[2:]
    keyword_args, args = parsers.parse_arguments(' '.join(args))
    if 'types' in args:
        return MDTeXDocument(Section(
            Bold('Types'),
            *[KeyValueItem(Bold(name), Code(code)) for name, code in AUTOBAHN_TYPES.items()]))
    string_type = keyword_args.get('type')
    code = keyword_args.get('code')
    code_range = keyword_args.get('range')
    hex_type = None
    collection = None
    if string_type is not None:
        hex_type = AUTOBAHN_TYPES.get(string_type)
        collection = db.ab_collection_map[hex_type]
    if code is None and code_range is None:
        all_strings = collection.fetchAll()
        if not len(all_strings) > 100:
            items = [KeyValueItem(Bold(f'0x{doc["_key"]}'.rjust(5)),
                                  Code(doc['string'])) for doc in all_strings]
        else:
            items = [Pre(', '.join([doc['string'] for doc in all_strings]))]
        return MDTeXDocument(Section(Bold(f'Strings for {string_type}[{hex_type}]'), *items))

    elif hex_type is not None and code is not None:
        db_key = code.split('x')[-1]
        string = collection.fetchDocument(db_key).getStore()['string']
        return MDTeXDocument(Section(Bold(f'String for {string_type}[{code}]'), Code(string)))

    elif hex_type is not None and code_range is not None:
        start, stop = [int(c.split('x')[-1]) for c in code_range.split('-')]
        keys = [str(i) for i in range(start, stop + 1)]
        documents = db.query(f'FOR doc IN @@collection '
                             'FILTER doc._key in @keys '
                             'RETURN doc',
                             bind_vars={'@collection': collection.name,
                                        'keys': keys})
        items = [KeyValueItem(Bold(f'0x{doc["_key"]}'.rjust(5)),
                              Code(doc['string'])) for doc in documents]
        return MDTeXDocument(Section(Bold(f'Strings for {string_type}[{hex_type}]'), *items))
