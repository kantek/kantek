import logging
import platform

import kantex
import telethon
from kantex.md import *
from telethon.errors import ChatSendStickersForbiddenError
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import InputStickerSetShortName, StickerSet, Channel

from kantek import Client
from kantek import Config
from kantek.utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.command('kantek')
async def kantek(client: Client, chat: Channel) -> KanTeXDocument:
    """Show information about Kantek.

    Examples:
        {cmd}
    """
    config = Config()
    stickerset: StickerSet = await client(GetStickerSetRequest(InputStickerSetShortName("kantek")))
    try:
        await client.send_file(chat, stickerset.documents[0])
    except ChatSendStickersForbiddenError:
        pass
    return KanTeXDocument(
        Section(f"{Bold('Kantek')} Userbot",
                KeyValueItem(Bold('Source'), config.source_url),
                KeyValueItem(Bold('Version'), client.kantek_version),
                KeyValueItem(Bold('Telethon version'), telethon.__version__),
                KeyValueItem(Bold('Python version'), platform.python_version()),
                KeyValueItem(Bold('KanTeX version'), kantex.__version__),
                KeyValueItem(Bold('Plugins loaded'),
                             len(client.plugin_mgr.commands) + len(client.plugin_mgr.events))))
