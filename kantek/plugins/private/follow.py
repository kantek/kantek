import logging
from typing import List

from aiohttp import InvalidURL

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
    if not args:
        return MDTeXDocument(Section('Error', Italic('No URL was provided')))
    sections = []
    for i, url in enumerate(args):
        if not url.startswith('http'):
            url: str = f'http://{url}'
        responses = []
        try:
            async with client.aioclient.get(url) as response:
                for resp in response.history:
                    responses.append(KeyValueItem(f'[{resp.status}]', f'{Code(resp.url)}'))
                responses.append(KeyValueItem(f'[{response.status}]', f'{Code(response.url)}'))
        except InvalidURL:
            responses.append(Italic(f'Invalid URL: {Code(url)}'))
        sections.append(SubSection(f'URL {i+1}', *responses))

    return MDTeXDocument(Section('Follow', *sections))
