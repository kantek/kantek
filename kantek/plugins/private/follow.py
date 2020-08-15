import logging
from typing import List

from aiohttp import InvalidURL, TooManyRedirects

from utils.client import Client
from kantex.md import *
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.command('follow', 'f')
async def follow(client: Client, args: List) -> KanTeXDocument:
    """Follow URL redirects until the end

    Arguments:
        `url`: The url to follow

    Examples:
        {cmd} https://kutt.it/spamwatch
        {cmd} src.kv2.dev
    """
    if not args:
        return KanTeXDocument(Section('Error', Italic('No URL was provided')))
    sections = []
    for i, url in enumerate(args):
        if not url.startswith('http'):
            url: str = f'http://{url}'
        responses = []
        try:
            async with client.aioclient.get(url) as response:
                responses.extend(format_responses([*response.history, response]))
        except TooManyRedirects as e:
            responses.extend(format_responses(e.history))
            responses.append(Italic(f'Too many redirects: {Code(url)}'))
        except InvalidURL:
            responses.append(Italic(f'Invalid URL: {Code(url)}'))
        sections.append(SubSection(f'URL {i + 1}', *responses))

    return KanTeXDocument(Section('Follow', *sections))


def format_responses(responses):
    result = []
    for resp in responses:
        result.append(KeyValueItem(f'[{resp.status}]', f'{Code(resp.url)}'))
    return result
