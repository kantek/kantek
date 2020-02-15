"""Query the SpamWatch API"""
import logging

from spamwatch.types import Permission
from telethon import events
from telethon.events import NewMessage

from config import cmd_prefix
from utils import helpers
from utils.client import KantekClient
from utils.mdtex import Bold, Code, KeyValueItem, MDTeXDocument, Section

__version__ = '0.1.0'

tlog = logging.getLogger('kantek-channel-log')

# TODO: Make this nice, this is just a skeleton so I have an easy way of creating tokens,
#  preferably clean this up at some point
@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}s(pam)?w(atch)?'))
async def sw(event: NewMessage.Event) -> None:
    """Command to create SpamWatch Tokens"""
    client: KantekClient = event.client
    if not client.sw:
        return
    keyword_args, args = await helpers.get_args(event)
    subcommand, *args = args

    result = ''

    if client.sw.permission != Permission.Root:
        await client.respond(event, MDTeXDocument(Section(Bold('Insufficient Permission'),
                                                          'Root Permission required.')))
    if subcommand == 'token':
        result = await _token(event, client, args, keyword_args)
    if result:
        await client.respond(event, result)


async def _token(event, client, args, keyword_args):
    command, *args = args

    userid = [uid for uid in args if isinstance(uid, int)]
    if not userid:
        return MDTeXDocument(Section(Bold('Missing Argument'),
                                     'A User ID is required.'))
    userid = userid[0]
    if command == 'create':
        from spamwatch.types import _permission_map
        permission = keyword_args.get('permission', 'User')
        permission = _permission_map.get(permission)
        token = client.sw.create_token(userid, permission)
        return MDTeXDocument(Section(Bold(f'SpamWatch Token'),
                                     KeyValueItem('ID', Code(token.id)),
                                     KeyValueItem('User', Code(token.userid)),
                                     KeyValueItem('Permission', token.permission.name),
                                     KeyValueItem('Token', Code(token.token))))
