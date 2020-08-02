import logging
from typing import List

from utils import helpers
from utils.mdtex import *
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.command('invitelink', 'il')
async def invitelink(args: List) -> MDTeXDocument:
    """Decode a invite link and output the Links creator, the chat id and the random part.

    Note: For channels the Link Creator is always 0

    Arguments:
        `invite_link`: The invite link to decode

    Examples:
        {cmd} https://t.me/joinchat/CkzknkNYuLsKbTc91GfhGw
    """
    link = args[0]
    link_creator, chatid, random_part = await helpers.resolve_invite_link(link)
    return MDTeXDocument(
        Section('Invite Link',
                KeyValueItem('Link Creator',
                             f'[{link_creator}](tg://user?id={link_creator})'),
                KeyValueItem('Chat ID', Code(chatid)),
                KeyValueItem('Random Part', Code(random_part))))
