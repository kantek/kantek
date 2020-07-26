"""Get information on a invite link."""
import logging
from typing import List

from utils.client import Client
from utils.mdtex import *
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.command('follow', 'f')
async def follow(client: Client, args: List) -> MDTeXDocument:
    """Follow URL redirects until the end

    Arguments:
        `url`: The url to follow

    Examples:
        {cmd} https://kutt.it/spamwatch
        {cmd} src.kv2.dev
    """
    link = args[0]
    return MDTeXDocument(
        Section('Follow',
                KeyValueItem(Bold('Original URL'), Code(link)),
                KeyValueItem(Bold('Followed URL'), Code(await client.resolve_url(link, base_domain=False)))))
