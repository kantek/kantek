"""Plugin to manage the autobahn"""
import asyncio
import logging
import os
import re

import logzero
from pyArango.document import Document
from telethon import events
from telethon.errors import MessageIdInvalidError
from telethon.events import NewMessage
from telethon.tl.custom import Message

from config import cmd_prefix
from database.arango import ArangoDB
from utils import helpers, parsers, constants
from utils.client import KantekClient
from utils.mdtex import Bold, Code, KeyValueItem, MDTeXDocument, Pre, Section, SubSection

__version__ = '0.2.1'

tlog = logging.getLogger('kantek-channel-log')
logger: logging.Logger = logzero.logger

AUTOBAHN_TYPES = {
    'bio': '0x0',
    'string': '0x1',
    'filename': '0x2',
    'channel': '0x3',
    'domain': '0x4',
    'file': '0x5',
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


def _sync_file_callback(received: int, total: int, msg: Message) -> None:
    loop = asyncio.get_event_loop()
    loop.create_task(_file_callback(received, total, msg))
    # msg.edit(args)


async def _file_callback(received: int, total: int, msg: Message) -> None:
    text = MDTeXDocument(Section(Bold('Downloading File'),
                                 KeyValueItem('Progress',
                                              f'{received / 1024 ** 2:.2f}/{total / 1024 ** 2:.2f}MB ({(received / total) * 100:.0f}%)')))
    try:
        await msg.edit(str(text))
    except MessageIdInvalidError as err:
        logger.error(err)


async def _add_string(event: NewMessage.Event, db: ArangoDB) -> MDTeXDocument:
    """Add a string to the Collection of its type"""
    client: KantekClient = event.client
    msg: Message = event.message
    args = msg.raw_text.split()[2:]
    _, args = parsers.parse_arguments(' '.join(args))
    string_type = args[0]
    strings = args[1:]
    added_items = []
    existing_items = []
    skipped_items = []
    hex_type = AUTOBAHN_TYPES.get(string_type)
    collection = db.ab_collection_map.get(hex_type)
    for string in strings:
        if hex_type is None or collection is None:
            continue
        if hex_type == '0x3':
            # remove any query parameters like ?start=
            # replace @ aswell since some spammers started using it, only Telegram X supports it
            _string = string.split('?')[0].replace('@', '')
            link_creator, chat_id, random_part = await helpers.resolve_invite_link(string)
            string = chat_id
            if string is None:
                try:
                    entity = await event.client.get_entity(_string)
                except constants.GET_ENTITY_ERRORS as err:
                    logger.error(err)
                    skipped_items.append(_string)
                    continue
                if entity:
                    string = entity.id
        elif hex_type == '0x4':
            string = await helpers.resolve_url(string)
            if string in constants.TELEGRAM_DOMAINS:
                skipped_items.append(string)
                continue
        # avoids "null" being added to the db
        if string is None:
            skipped_items.append(string)
            continue

        existing_one = collection.fetchByExample({'string': string}, batchSize=1)

        if not existing_one:
            collection.add_string(string)
            added_items.append(Code(string))
        else:
            existing_items.append(Code(string))

    if not strings and hex_type == '0x5':
        if msg.is_reply:
            reply_msg: Message = await msg.get_reply_message()
            if reply_msg.file:
                await msg.edit('Downloading file, this may take a while.')

                dl_filename = await reply_msg.download_media('tmp/blacklisted_file',
                                                             progress_callback=lambda r, t: _sync_file_callback(r, t, msg))
                file_hash = await helpers.hash_file(dl_filename)
                os.remove(dl_filename)
                await msg.delete()
                existing_one = collection.fetchByExample({'string': file_hash}, batchSize=1)

                short_hash = f'{file_hash[:15]}[...]'
                if not existing_one:
                    collection.add_string(file_hash)
                    added_items.append(Code(short_hash))
                else:
                    existing_items.append(Code(short_hash))
            else:
                return MDTeXDocument(Section(Bold('Error'), 'Need to reply to a file'))
        else:
            return MDTeXDocument(Section(Bold('Error'), 'Need to reply to a file'))

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

    hex_type = None
    collection = None
    if string_type is not None:
        hex_type = AUTOBAHN_TYPES.get(string_type)
        collection = db.ab_collection_map[hex_type]
    if code is None:
        all_strings = collection.fetchAll()
        if not len(all_strings) > 100:
            items = [KeyValueItem(Bold(f'0x{doc["_key"]}'.rjust(5)),
                                  Code(doc['string'])) for doc in all_strings]
        else:
            items = [Pre(', '.join([doc['string'] for doc in all_strings]))]
        return MDTeXDocument(Section(Bold(f'Items for type: {string_type}[{hex_type}]'), *items))

    elif hex_type is not None and code is not None:
        if isinstance(code, int):
            string = collection.fetchDocument(code).getStore()['string']
            return MDTeXDocument(Section(Bold(f'Items for type: {string_type}[{hex_type}] code: {code}'), Code(string)))
        elif isinstance(code, range) or isinstance(code, list):
            keys = [str(i) for i in code]
            documents = db.query(f'FOR doc IN @@collection '
                                 'FILTER doc._key in @keys '
                                 'RETURN doc',
                                 bind_vars={'@collection': collection.name,
                                            'keys': keys})
            items = [KeyValueItem(Bold(f'0x{doc["_key"]}'.rjust(5)),
                                  Code(doc['string'])) for doc in documents]
            return MDTeXDocument(
                Section(Bold(f'Items for for type: {string_type}[{hex_type}]'), *items))
