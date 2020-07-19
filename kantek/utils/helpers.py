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
from PIL import Image
from telethon import utils
from telethon.events import NewMessage
from telethon.tl.custom import Message
from telethon.tl.types import User, DocumentAttributeFilename

from utils import parsers

INVITELINK_PATTERN = re.compile(r'(?:joinchat|join)(?:/|\?invite=)(.*|)')

MESSAGE_LINK_PATTERN = re.compile(r't\.me/(?:c/)?(?P<chat>\w+)/(?P<id>\d+)')

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


def hash_file(file: bytes):
    hasher = hashlib.sha512()
    hasher.update(file)
    return hasher.hexdigest()


async def hash_photo(photo):
    loop = asyncio.get_event_loop()
    pil_photo = Image.open(BytesIO(photo))
    photo_hash = await loop.run_in_executor(None, photohash.average_hash, pil_photo)
    return str(photo_hash)


async def get_linked_message(client, link):
    match = MESSAGE_LINK_PATTERN.search(link)
    if not match:
        return None
    else:
        chat = match.group('chat')
        if chat.isnumeric():
            chat = int(chat)
        else:
            chat = f'@{chat}'
        msg_id = int(match.group('id'))
        return await client.iter_messages(entity=chat, ids=[msg_id]).__anext__()


async def textify_message(msg: Message):
    message = []

    if msg.photo:
        message.append('[photo]')
    elif msg.sticker:
        message.append('[sticker]')
    elif msg.document:
        filename = [attr.file_name for attr in msg.document.attributes if isinstance(attr, DocumentAttributeFilename)]
        message.append(f'[document:{filename[0] if filename else ""}:{msg.document.mime_type}]')
    elif msg.audio:
        message.append('[audio]')
    elif msg.contact:
        message.append('[contact]')
    elif msg.sticker:
        message.append('[sticker]')
    if message:
        message.append('')
    message.append(msg.text if msg.text else '[no text/caption]')
    return '\n'.join(message)
