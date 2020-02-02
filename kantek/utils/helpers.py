"""Helper functions to aid with different tasks that dont require a client."""
import asyncio
import csv
import hashlib
import logging
import re
import urllib
from io import BytesIO
from typing import Dict, List, Tuple

import logzero
import photohash
import requests
from PIL import Image
from faker import Faker
from requests import ConnectionError, ReadTimeout
from telethon import utils
from telethon.events import NewMessage
from telethon.tl.types import User

from utils import parsers

INVITELINK_PATTERN = re.compile(r'(?:joinchat|join)(?:/|\?invite=)(.*|)')

logger: logging.Logger = logzero.logger


async def get_full_name(user: User) -> str:
    """Return first_name + last_name if last_name exists else just first_name

    Args:
        user: The user

    Returns:
        The combined names
    """
    return str(user.first_name + ' ' + (user.last_name or ''))


async def get_args(event: NewMessage.Event) -> Tuple[Dict[str, str], List[str]]:
    """Get arguments from a event

    Args:
        event: The event

    Returns:
        Parsed arguments as returned by parser.parse_arguments()
    """
    _args = event.message.raw_text.split()[1:]
    return parsers.parse_arguments(' '.join(_args))


async def rose_csv_to_dict(filename: str) -> List[Dict[str, str]]:
    """Convert a fedban list from Rose to a json that can be imported into ArangoDB

    Args:
        filename: The name of the csv

    Returns:

    """
    bans = []
    with open(filename, encoding='utf-8', newline='') as f:  #
        csv_file = csv.reader(f, delimiter=',')
        # skip the header
        next(csv_file, None)
        for line in csv_file:
            _id = line[0]
            reason = line[-1]
            bans.append({'_key': _id, 'id': _id, 'reason': reason})
    return bans


async def resolve_invite_link(link):
    """Method to work around a bug in telethon 1.6 and 1.7 that makes the resolve_invite_link method
    unable to parse tg://invite style links

    This is temporary and will be removed

    Args:
        link:

    Returns:
        Same as telethons method

    """
    encoded_link = re.search(INVITELINK_PATTERN, link)
    if encoded_link is not None:
        encoded_link = encoded_link.group(1)
        invite_link = f't.me/joinchat/{encoded_link}'
        return utils.resolve_invite_link(invite_link)
    else:
        return None, None, None


async def netloc(url: str) -> str:
    return urllib.parse.urlparse(url).netloc


async def resolve_url(url: str, base_domain: bool = True) -> str:
    """Follow all redirects and return the base domain

    Args:
        url: The url

    Returns:
        The base comain as given by urllib.parse
    """
    faker = Faker()
    headers = {'User-Agent': faker.user_agent()}
    if not url.startswith('http'):
        url = f'http://{url}'
    try:
        req = requests.get(url, headers=headers, timeout=2)
        url = req.url
    except (ConnectionError, ReadTimeout) as err:
        logger.warning(err)
    netloc = urllib.parse.urlparse(url).netloc
    # split up the result to only get the base domain
    # www.sitischu.com => sitischu.com
    _base_domain = netloc.split('.', maxsplit=netloc.count('.') - 1)[-1]
    if _base_domain and base_domain:
        url = _base_domain
    return url


def hash_file(file: bytes):
    hasher = hashlib.sha512()
    hasher.update(file)
    return hasher.hexdigest()


async def hash_photo(photo):
    loop = asyncio.get_event_loop()
    pil_photo = Image.open(BytesIO(photo))
    photo_hash = await loop.run_in_executor(None, photohash.average_hash, pil_photo)
    return str(photo_hash)
