"""File containing the Custom TelegramClient"""
import datetime
import time
from typing import Optional, Union

from telethon import TelegramClient
from telethon.events import NewMessage
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.patched import Message
from telethon.tl.types import ChatBannedRights

import config
from database.arango import ArangoDB
from utils.mdtex import FormattedBase, MDTeXDocument, Section
from utils.pluginmgr import PluginManager
from utils.strafregister import Strafregister


class KantekClient(TelegramClient):  # pylint: disable = R0901, W0223
    """Custom telethon client that has the plugin manager as attribute."""
    plugin_mgr: Optional[PluginManager] = None
    db: Optional[ArangoDB] = None
    kantek_version: str = ''
    sr = Strafregister(config.strafregister_file)

    async def respond(self, event: NewMessage.Event,
                      msg: Union[str, FormattedBase, Section, MDTeXDocument],
                      reply: bool = True) -> Message:
        """Respond to the message an event caused or to the message that was replied to

        Args:
            event: The event of the message
            msg: The message text
            reply: If it should reply to the message that was replied to

        Returns: None

        """
        msg = str(msg)
        if reply:
            return await event.respond(msg, reply_to=(event.reply_to_msg_id or event.message.id))
        else:
            return await event.respond(msg, reply_to=event.message.id)

    async def gban(self, uid: Union[int, str], reason: str, fedban: bool = True):
        """Command to gban a user

        Args:
            uid: User ID
            reason: Ban reason
            fedban: If /fban should be used

        Returns: None

        """
        # if the user account is deleted this can be None
        if uid is None:
            return
        await self.sr.log(Strafregister.BAN, uid, reason)
        await self.send_message(
            config.gban_group,
            f'<a href="tg://user?id={uid}">{uid}</a>', parse_mode='html')
        await self.send_message(
            config.gban_group,
            f'/ban {uid} {reason}')
        if fedban:
            await self.send_message(
                config.gban_group,
                f'/fban {uid} {reason}')
        time.sleep(0.5)
        await self.send_read_acknowledge(config.gban_group,
                                         max_id=1000000,
                                         clear_mentions=True)
        data = {'_key': str(uid),
                'id': str(uid),
                'reason': reason}
        self.db.query('UPSERT {"_key": @ban.id} '
                      'INSERT @ban '
                      'UPDATE {"reason": @ban.reason} '
                      'IN BanList', bind_vars={'ban': data})

    async def ungban(self, uid: Union[int, str], fedban: bool = True):
        """Command to gban a user

        Args:
            uid: User ID
            fedban: If /unfban should be used

        Returns: None

        """
        await self.sr.log(Strafregister.UNBAN, uid)
        await self.send_message(
            config.gban_group,
            f'<a href="tg://user?id={uid}">{uid}</a>', parse_mode='html')
        await self.send_message(
            config.gban_group,
            f'/unban {uid}')
        if fedban:
            await self.send_message(
                config.gban_group,
                f'/unfban {uid}')
        time.sleep(0.5)
        await self.send_read_acknowledge(config.gban_group,
                                         max_id=1000000,
                                         clear_mentions=True)

        self.db.query('REMOVE {"_key": @uid} '
                      'IN BanList', bind_vars={'uid': str(uid)})

    async def ban(self, chat, uid):
        """Bans a user from a chat."""
        await self(EditBannedRequest(
            chat, uid, ChatBannedRights(
                until_date=datetime.datetime(2038, 1, 1),
                view_messages=True
            )
        ))
