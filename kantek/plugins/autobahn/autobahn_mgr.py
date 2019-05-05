"""Plugin to manage the autobahn"""
import logging
from typing import List, Union

from pyArango.document import Document
from telethon import events
from telethon.events import NewMessage
from telethon.tl.patched import Message

from config import cmd_prefix
from database.arango import ArangoDB
from utils import parsers
from utils.client import KantekClient
from utils.mdtex import Bold, Code, Italic, KeyValueItem, MDTeXDocument, Pre, Section, SubSection

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

    return MDTeXDocument(Section(Bold('Added Items:'),
                                 *(await _format_items(added_items))))


async def _del_string(event: NewMessage.Event, db: ArangoDB) -> MDTeXDocument:
    """Add a string to the Collection of its type"""
    msg: Message = event.message
    args = msg.raw_text.split()[2:]
    keyword_args, args = parsers.parse_arguments(' '.join(args))
    strings = [s.split(';', maxsplit=1) for s in args]
    removed_items = []
    for item in strings:
        if len(item) != 2:
            continue
        string_type, string = item
        hex_type = AUTOBAHN_TYPES.get(string_type)
        collection = db.ab_collection_map.get(hex_type)
        if hex_type is None or collection is None:
            continue

        existing_one: Document = collection.fetchFirstExample({'string': string})
        if existing_one:
            existing_one.delete()
            removed_items.append(item)

    return MDTeXDocument(Section(Bold('Deleted Items:'),
                                 *(await _format_items(removed_items))))


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
    if string_type and code is None and code_range is None:
        hex_type = AUTOBAHN_TYPES.get(string_type)
        if hex_type is not None:
            collection = db.ab_collection_map[hex_type]
            all_strings = collection.fetchAll()
            if not len(all_strings) > 100:
                items = [KeyValueItem(Bold(f'0x{doc["_key"]}'.rjust(5)),
                                      Code(doc['string'])) for doc in all_strings]
            else:
                items = [Pre(', '.join([doc['string'] for doc in all_strings]))]
            return MDTeXDocument(Section(Bold(f'Strings for {string_type}[{hex_type}]'), *items))

    if string_type is not None and code is not None:
        hex_type = AUTOBAHN_TYPES.get(string_type)
        if hex_type is not None:
            collection = db.ab_collection_map[hex_type]
            db_key = code.split('x')[-1]
            string = collection.fetchDocument(db_key).getStore()['string']
            return MDTeXDocument(Section(Bold(f'String for {string_type}[{code}]'), Code(string)))

    if string_type is not None and code_range is not None:
        hex_type = AUTOBAHN_TYPES.get(string_type)
        if hex_type is not None:
            collection = db.ab_collection_map[hex_type]
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


async def _format_items(items: List[List[str]]) -> List[Union[Section, Italic]]:
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
    if sections:
        return sections
    else:
        return [Italic('None')]
