"""Plugin to handle global bans"""
from typing import Optional, List

from telethon.tl.custom import Message

from database.database import Database
from utils.client import Client
from utils.mdtex import *
from utils.pluginmgr import k, Command


@k.command('ungban')
async def ungban(client: Client, db: Database, msg: Message, args: List) -> Optional[MDTeXDocument]:
    """Globally unban a User

    This does not unban them from any groups. It simply removes their ban from the database, api and any bots in the gban group.

    Arguments:
        `ids`: User IDs to ungban.

    Examples:
        {cmd} 777000
    """
    await msg.delete()

    users_to_unban = [*args]
    if msg.is_reply:
        reply_msg: Message = await msg.get_reply_message()
        uid = reply_msg.from_id
        users_to_unban.append(uid)

    unbanned_users = []
    for uid in users_to_unban:
        if await db.banlist.get(uid):
            await client.ungban(uid)
            unbanned_users.append(str(uid))
    if unbanned_users:
        return MDTeXDocument(
            Section('Un-GBanned Users',
                    KeyValueItem(Bold('IDs'), Code(', '.join(unbanned_users)))))
