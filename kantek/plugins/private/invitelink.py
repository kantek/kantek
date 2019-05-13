"""Get information on a invite link."""
import logging

from telethon import events
from telethon.events import NewMessage

from config import cmd_prefix
from utils import helpers
from utils.client import KantekClient
from utils.mdtex import Bold, Code, KeyValueItem, MDTeXDocument, Section

__version__ = '0.1.0'

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}i(nvite)?l(ink)?'))
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
