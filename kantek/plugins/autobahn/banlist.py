"""Plugin to manage the banlist of the bot."""
import csv
import logging
import os
import time
from typing import List

from spamwatch.types import Ban, Permission
from telethon.events import NewMessage
from telethon.tl.custom import Message

from database.arango import ArangoDB
from utils import helpers, parsers
from utils.client import KantekClient
from utils.mdtex import Bold, Code, Italic, KeyValueItem, MDTeXDocument, Section
from utils.pluginmgr import k, Command

tlog = logging.getLogger('kantek-channel-log')

SWAPI_SLICE_LENGTH = 50


@k.command('b(an)?l(ist)?')
async def banlist(client: KantekClient, db: ArangoDB, msg: Message, event: Command) -> None:
    """Command to query and manage the banlist."""
    # TODO Replaced with subcomamnd implementation
    args = msg.raw_text.split()[1:]
    response = ''
    if not args:
        pass
    elif args[0] == 'query':
        response = await _query_banlist(event, db)
    elif args[0] == 'import':
        waiting_message = await client.respond(event, 'Importing bans. This might take a while.')
        response = await _import_banlist(event, db)
        await waiting_message.delete()
    elif args[0] == 'export':
        waiting_message = await client.respond(event, 'Exporting bans. This might take a while.')
        response = await _export_banlist(event, db)
        await waiting_message.delete()
    if response:
        await client.respond(event, response)


async def _query_banlist(event: NewMessage.Event, db: ArangoDB) -> MDTeXDocument:
    msg: Message = event.message
    args = msg.raw_text.split()[2:]
    keyword_args, args = parsers.parse_arguments(' '.join(args))
    reason = keyword_args.get('reason')
    users = []
    if args:
        uids = [str(uid) for uid in args]
        users = db.query('For doc in BanList '
                         'FILTER doc._key in @ids '
                         'RETURN doc', bind_vars={'ids': uids})
        query_results = [KeyValueItem(Code(user['id']), user['reason'])
                         for user in users] or [Italic('None')]
    elif reason is not None:
        result: List[int] = db.query('FOR doc IN BanList '
                                     'FILTER doc.reason LIKE @reason '
                                     'COLLECT WITH COUNT INTO length '
                                     'RETURN length', bind_vars={'reason': reason}).result
        query_results = [KeyValueItem(Bold('Count'), Code(result[0]))]
    else:
        result: List[int] = db.query('FOR doc IN BanList '
                                     'COLLECT WITH COUNT INTO length '
                                     'RETURN length').result

        query_results = [KeyValueItem(Bold('Total Count'), Code(result[0]))]
    return MDTeXDocument(Section(Bold('Query Results'), *query_results))


async def _import_banlist(event: NewMessage.Event, db: ArangoDB) -> MDTeXDocument:
    msg: Message = event.message
    client: KantekClient = event.client
    filename = 'tmp/banlist_import.csv'
    if msg.is_reply:  # pylint: disable = R1702
        reply_msg: Message = await msg.get_reply_message()
        _, ext = os.path.splitext(reply_msg.document.attributes[0].file_name)
        if ext == '.csv':
            await reply_msg.download_media('tmp/banlist_import.csv')
            start_time = time.time()
            _banlist = await helpers.rose_csv_to_dict(filename)
            if _banlist:
                db.query('FOR ban in @banlist '
                         'UPSERT {"_key": ban.id} '
                         'INSERT ban '
                         'UPDATE {"reason": ban.reason} '
                         'IN BanList', bind_vars={'banlist': _banlist})
                if client.sw and client.sw.permission in [Permission.Admin, Permission.Root]:
                    bans = {}
                    for b in _banlist:
                        bans[b['reason']] = bans.get(b['reason'], []) + [b['id']]
                    admin_id = (await client.get_me()).id
                    for reason, uids in bans.items():
                        uids_copy = uids[:]
                        while uids_copy:
                            client.sw.add_bans([Ban(int(uid), reason, admin_id)
                                                for uid in uids_copy[:SWAPI_SLICE_LENGTH]])
                            uids_copy = uids_copy[SWAPI_SLICE_LENGTH:]

            stop_time = time.time() - start_time
            return MDTeXDocument(Section(Bold('Import Result'),
                                         f'Added {len(_banlist)} entries.'),
                                 Italic(f'Took {stop_time:.02f}s'))
        else:
            return MDTeXDocument(Section(Bold('Error'), 'File is not a CSV'))


async def _export_banlist(event: NewMessage.Event, db: ArangoDB) -> None:
    client: KantekClient = event.client
    chat = await event.get_chat()
    users = db.query('For doc in BanList '
                     'RETURN doc')
    os.makedirs('tmp/', exist_ok=True)
    start_time = time.time()
    with open('tmp/banlist_export.csv', 'w') as f:
        f.write('id,reason\n')
        cwriter = csv.writer(f)
        for user in users:
            cwriter.writerow([user['id'], user['reason']])
    stop_time = time.time() - start_time
    await client.send_file(chat, 'tmp/banlist_export.csv',
                           caption=str(Italic(f'Took {stop_time:.02f}s')))
