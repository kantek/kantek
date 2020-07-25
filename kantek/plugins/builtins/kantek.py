"""Plugin to get information about kantek."""
import logging
import platform

import telethon
from telethon.errors import ChatSendStickersForbiddenError
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import InputStickerSetShortName, StickerSet, Channel

from utils.client import KantekClient
from utils.mdtex import *
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.command('kantek')
async def kantek(client: KantekClient, chat: Channel) -> MDTeXDocument:
    """Show information about kantek.

    Examples:
        {cmd}
    """
    stickerset: StickerSet = await client(GetStickerSetRequest(InputStickerSetShortName("kantek")))
    try:
        await client.send_file(chat, stickerset.documents[0])
    except ChatSendStickersForbiddenError:
        pass
    return MDTeXDocument(
        Section(f"{Bold('kantek')} userbot",
                KeyValueItem(Bold('source'), 'src.kv2.dev'),
                KeyValueItem(Bold('version'), client.kantek_version),
                KeyValueItem(Bold('telethon version'), telethon.__version__),
                KeyValueItem(Bold('python version'), platform.python_version()),
                KeyValueItem(Bold('plugins loaded'),
                             len(client.plugin_mgr.commands) + len(client.plugin_mgr.events))))
