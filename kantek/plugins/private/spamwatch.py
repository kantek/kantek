"""Query the SpamWatch API"""
import logging
from typing import List, Dict

from spamwatch.types import Permission
from telethon.tl.patched import Message

from utils.client import KantekClient
from utils.mdtex import *
from utils.pluginmgr import k, Command

tlog = logging.getLogger('kantek-channel-log')


# TODO: Make this nice, this is just a skeleton so I have an easy way of creating tokens,
#  preferably clean this up at some point
@k.command('s(pam)?w(atch)?')
async def sw(client: KantekClient, args: List, kwargs: Dict, event: Command) -> None:
    """Command to create SpamWatch Tokens"""
    if not client.sw:
        return
    subcommand, *args = args

    result = ''

    if client.sw.permission != Permission.Root:
        await client.respond(event, MDTeXDocument(Section(Bold('Insufficient Permission'),
                                                          'Root Permission required.')))
    if subcommand == 'token':
        result = await _token(event, client, args, kwargs)
    if result:
        await client.respond(event, result)


async def _token(event, client, args, keyword_args):
    command, *args = args
    msg: Message = event.message
    userid = [uid for uid in args if isinstance(uid, int)]
    if not userid:
        if msg.is_reply:
            reply_message: Message = await msg.get_reply_message()
            userid = reply_message.from_id
        else:
            return MDTeXDocument(Section(Bold('Missing Argument'),
                                         'A User ID is required.'))
    else:
        userid = userid[0]
    if command == 'create':
        from spamwatch.types import _permission_map  # pylint: disable = C0415
        permission = keyword_args.get('permission', 'User')
        permission = _permission_map.get(permission)
        token = client.sw.create_token(userid, permission)
        return MDTeXDocument(Section(Bold('SpamWatch Token'),
                                     KeyValueItem('ID', Code(token.id)),
                                     KeyValueItem('User', Code(token.userid)),
                                     KeyValueItem('Permission', token.permission.name),
                                     KeyValueItem('Token', Code(token.token))),
                             Section(Bold('Links'),
                                     KeyValueItem('Endpoint', client.sw_url.split('://')[-1]),
                                     KeyValueItem('Documentation', 'docs.spamwat.ch')))
