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


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}f(ollow)?'))
async def follow(event: NewMessage.Event) -> None:
    """Command to follow where a URL redirects to."""
    client: KantekClient = event.client
    _, args = await helpers.get_args(event)
    link = args[0]
    await client.respond(event, MDTeXDocument(
        Section(Bold('Follow'),
                KeyValueItem(Bold('Original URL'), Code(link)),
                KeyValueItem(Bold('Followed URL'), Code(await client.resolve_url(link, base_domain=False))))))
