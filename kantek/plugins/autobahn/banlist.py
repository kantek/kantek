""""""
import logging

from telethon import events
from telethon.events import NewMessage
from telethon.tl.patched import Message
from telethon.tl.types import Channel

from config import cmd_prefix
from database.arango import ArangoDB
from utils import parsers
from utils.client import KantekClient
from utils.mdtex import Bold, Code, Italic, KeyValueItem, MDTeXDocument, Section

__version__ = '0.1.0'

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}b(an)?l(ist)?'))
async def banlist(event: NewMessage.Event) -> None:
    """"""
    chat: Channel = event.chat
    client: KantekClient = event.client
    msg: Message = event.message
    db: ArangoDB = client.db
    args = msg.raw_text.split()[1:]
    response = ''
    if not args:
        pass
    elif args[0] == 'query' and len(args) > 1:
        response = await _query_banlist(event, db)

    if response:
        await client.respond(event, response)


async def _query_banlist(event: NewMessage.Event, db: ArangoDB) -> MDTeXDocument:
    msg: Message = event.message
    args = msg.raw_text.split()[2:]
    keyword_args, args = parsers.parse_arguments(' '.join(args))
    reason = keyword_args.get('reason')
    users = []
    if args:
        users = db.query('For doc in BanList '
                         'FILTER doc._key in @ids '
                         'RETURN doc', bind_vars={'ids': args})
        query_results = [KeyValueItem(Code(user['id']), user['reason'])
                         for user in users] or [Italic('None')]
    if reason is not None:
        result = db.query('FOR doc IN BanList '
                          'FILTER doc.reason LIKE @reason '
                          'COLLECT WITH COUNT INTO length '
                          'RETURN length', bind_vars={'reason': reason})
        query_results = [KeyValueItem(Bold('Count'), Code(result))]
    return MDTeXDocument(Section(Bold('Query Results'), *query_results))
