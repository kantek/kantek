"""Plugin to get information about a channel."""
import logging
from typing import Optional

from telethon.tl.types import Channel, User

from utils.client import Client
from utils.mdtex import *
from utils.pluginmgr import k, Command
from utils.tags import Tags

tlog = logging.getLogger('kantek-channel-log')


@k.command('info')
async def info(client: Client, tags: Tags, chat: Channel, event: Command) -> Optional[MDTeXDocument]:
    """Show information about a group or channel.

    Examples:
        {cmd}
    """
    if event.is_private:
        await event.delete()
        return
    chat_info = Section(f'info for {chat.title}:',
                        KeyValueItem(Bold('title'), Code(chat.title)),
                        KeyValueItem(Bold('chat_id'), Code(event.chat_id)),
                        KeyValueItem(Bold('access_hash'), Code(chat.access_hash)),
                        KeyValueItem(Bold('creator'), Code(chat.creator)),
                        KeyValueItem(Bold('broadcast'), Code(chat.broadcast)),
                        KeyValueItem(Bold('megagroup'), Code(chat.megagroup)),
                        KeyValueItem(Bold('min'), Code(chat.min)),
                        KeyValueItem(Bold('username'), Code(chat.username)),
                        KeyValueItem(Bold('verified'), Code(chat.verified)),
                        KeyValueItem(Bold('version'), Code(chat.version)),
                        )

    bot_accounts = 0
    total_users = 0
    deleted_accounts = 0
    user: User
    async for user in client.iter_participants(chat):
        total_users += 1
        if user.bot:
            bot_accounts += 1
        if user.deleted:
            deleted_accounts += 1

    user_stats = Section('user stats:',
                         KeyValueItem(Bold('total_users'), Code(total_users)),
                         KeyValueItem(Bold('bots'), Code(bot_accounts)),
                         KeyValueItem(Bold('deleted_accounts'), Code(deleted_accounts)))

    data = []
    data += [KeyValueItem(Bold(key), value) for key, value in tags.named_tags.items()]
    tags = Section('tags:', *data or [Italic('None')])
    return MDTeXDocument(chat_info, user_stats, tags)
