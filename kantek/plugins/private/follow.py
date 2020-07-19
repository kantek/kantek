"""Get information on a invite link."""
import logging
from typing import List, Dict

from telethon.tl.patched import Message
from telethon.tl.types import Channel

from utils.client import KantekClient
from utils.mdtex import Bold, Code, KeyValueItem, MDTeXDocument, Section
from utils.pluginmgr import k, Command

tlog = logging.getLogger('kantek-channel-log')


@k.command('f(ollow)?')
async def follow(client: KantekClient, chat: Channel, msg: Message,
                  args: List, kwargs: Dict, event: Command) -> None:
    """Command to follow where a URL redirects to."""
    link = args[0]
    await client.respond(event, MDTeXDocument(
        Section(Bold('Follow'),
                KeyValueItem(Bold('Original URL'), Code(link)),
                KeyValueItem(Bold('Followed URL'), Code(await client.resolve_url(link, base_domain=False))))))
