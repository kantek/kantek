"""Get information on a invite link."""
import logging
from typing import List

from utils.client import KantekClient
from utils.mdtex import Bold, Code, KeyValueItem, MDTeXDocument, Section
from utils.pluginmgr import k, Command

tlog = logging.getLogger('kantek-channel-log')


@k.command('f(ollow)?')
async def follow(client: KantekClient, args: List, event: Command) -> None:
    """Command to follow where a URL redirects to."""
    link = args[0]
    await client.respond(event, MDTeXDocument(
        Section(Bold('Follow'),
                KeyValueItem(Bold('Original URL'), Code(link)),
                KeyValueItem(Bold('Followed URL'), Code(await client.resolve_url(link, base_domain=False))))))
