"""Get information on a invite link."""
import logging
from typing import List

from utils import helpers
from utils.mdtex import *
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.command('i(nvite)?l(ink)?')
async def invitelink(args: List) -> MDTeXDocument:
    """Command to get link creator, chatid and the random part of an invite link."""
    link = args[0]
    link_creator, chatid, random_part = await helpers.resolve_invite_link(link)
    return MDTeXDocument(
        Section(Bold('Invite Link'),
                KeyValueItem('Link Creator',
                             f'[{link_creator}](tg://user?id={link_creator})'),
                KeyValueItem('Chat ID', Code(chatid)),
                KeyValueItem('Random Part', Code(random_part))))
