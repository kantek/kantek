"""Get information on a invite link."""
import logging
from typing import List, Dict

from telethon.tl.types import Channel, Message

from utils import helpers
from utils.client import KantekClient
from utils.mdtex import Bold, Code, KeyValueItem, MDTeXDocument, Section
from utils.pluginmgr import k, Command

tlog = logging.getLogger('kantek-channel-log')


@k.command('i(nvite)?l(ink)?')
async def invitelink(client: KantekClient, chat: Channel, msg: Message,
                     args: List, kwargs: Dict, event: Command) -> None:
    """Command to get link creator, chatid and the random part of an invite link."""
    link = args[0]
    link_creator, chatid, random_part = await helpers.resolve_invite_link(link)
    await client.respond(event, MDTeXDocument(
        Section(Bold('Invite Link'),
                KeyValueItem('Link Creator',
                             f'[{link_creator}](tg://user?id={link_creator})'),
                KeyValueItem('Chat ID', Code(chatid)),
                KeyValueItem('Random Part', Code(random_part)))))
