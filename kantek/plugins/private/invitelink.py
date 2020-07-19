"""Get information on a invite link."""
import logging

from telethon.events import NewMessage

from utils import helpers
from utils.client import KantekClient
from utils.mdtex import Bold, Code, KeyValueItem, MDTeXDocument, Section

__version__ = '0.1.0'

from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.command('i(nvite)?l(ink)?')
async def invitelink(event: NewMessage.Event) -> None:
    """Command to get link creator, chatid and the random part of an invite link."""
    client: KantekClient = event.client
    _, args = await helpers.get_args(event)
    link = args[0]
    link_creator, chatid, random_part = await helpers.resolve_invite_link(link)
    await client.respond(event, MDTeXDocument(
        Section(Bold('Invite Link'),
                KeyValueItem('Link Creator',
                             f'[{link_creator}](tg://user?id={link_creator})'),
                KeyValueItem('Chat ID', Code(chatid)),
                KeyValueItem('Random Part', Code(random_part)))))
