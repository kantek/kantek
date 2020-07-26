"""Plugin to manage the banlist of the bot."""
import codecs
import csv
import logging
import os
import time
from io import BytesIO
from typing import List

from spamwatch.types import Ban, Permission
from telethon.tl.custom import Message
from telethon.tl.types import DocumentAttributeFilename

from database.arango import ArangoDB
from utils import helpers
from utils.client import Client
from utils.mdtex import *
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')

SWAPI_SLICE_LENGTH = 50


@k.command('banlist', 'bl')
async def banlist() -> None:
    """Query, Import or Export the banlist."""
    pass


@banlist.subcommand()
async def query(db: ArangoDB, args, kwargs) -> MDTeXDocument:
    """Query the banlist for the total ban count, a specific user or a ban reason.

    If no arguments are provided the total count will be returned.
    If a list of User IDs is provided their ban reasons will be listed next to their ID.
    If a reason is provided the total amount of banned users for that ban reason will be returned.

    Examples:
        {cmd} 777000 172811422
        {cmd} reason: "spam[gban]"
        {cmd} reason: "Kriminalamt %"
        {cmd}
    """
    reason = kwargs.get('reason')
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
    return MDTeXDocument(Section('Query Results', *query_results))


@banlist.subcommand()
async def import_(client: Client, db: ArangoDB, msg: Message) -> MDTeXDocument:
    """Import a CSV to the banlist.

    The CSV file should end in .csv and have a `id` and `reason` column

    Examples:
        {cmd}
    """
    if msg.is_reply:  # pylint: disable = R1702
        reply_msg: Message = await msg.get_reply_message()
        _, ext = os.path.splitext(reply_msg.document.attributes[0].file_name)
        if ext == '.csv':
            data = await reply_msg.download_media(bytes)
            start_time = time.time()
            _banlist = await helpers.rose_csv_to_dict(data)
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
            return MDTeXDocument(Section('Import Result',
                                         f'Added {len(_banlist)} entries.'),
                                 Italic(f'Took {stop_time:.02f}s'))
        else:
            return MDTeXDocument(Section('Error',
                                         'File is not a CSV'))


@banlist.subcommand()
async def export(client: Client, db: ArangoDB, chat, msg, kwargs) -> None:
    """Export the banlist as CSV.

    The format is `id,reason` and can be imported into most bots.

    Examples:
        {cmd}
    """
    start_time = time.time()
    with_diff = kwargs.get('diff', False)

    if with_diff and msg.is_reply:  # pylint: disable = R1702
        reply_msg: Message = await msg.get_reply_message()
        _, ext = os.path.splitext(reply_msg.document.attributes[0].file_name)
        if ext == '.csv':
            data = await reply_msg.download_media(bytes)
            _banlist = await helpers.rose_csv_to_dict(data)
            _banlist = [u['id'] for u in _banlist]
    else:
        _banlist = None

    if with_diff:
        users = db.query('For doc in BanList '
                         'FILTER doc._key not in @ids '
                         'RETURN doc', bind_vars={'ids': _banlist})
    else:
        users = db.query('For doc in BanList '
                         'RETURN doc')
    export = BytesIO()
    wrapper_file = codecs.getwriter('utf-8')(export)
    cwriter = csv.writer(wrapper_file, lineterminator='\n')
    for user in users:
        cwriter.writerow([user['id'], user['reason']])
    stop_time = time.time() - start_time
    await client.send_file(chat, export.getvalue(),
                           attributes=[DocumentAttributeFilename('banlist_export.csv')],
                           caption=str(Italic(f'Took {stop_time:.02f}s')))
