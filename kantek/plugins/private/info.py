import logging
from typing import Optional

from telethon.tl.types import Channel, User

from kantek import Client
from kantex.md import *
from kantek import k, Command
from kantek.utils.tags import Tags

tlog = logging.getLogger('kantek-channel-log')


@k.command('info')
async def info(client: Client, tags: Tags, chat: Channel, event: Command) -> Optional[KanTeXDocument]:
    """Show information about a group or channel.

    Examples:
        {cmd}
    """
    if event.is_private:
        await event.delete()
        return
    chat_info = Section(f'Info for {chat.title}:',
                        KeyValueItem('title', Code(chat.title)),
                        KeyValueItem('chat_id', Code(event.chat_id)),
                        KeyValueItem('broadcast', Code(chat.broadcast)),
                        KeyValueItem('megagroup', Code(chat.megagroup)),
                        KeyValueItem('username', Code(chat.username)) if chat.username else None,
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

    user_stats = Section('User stats:',
                         KeyValueItem('total_users', Code(total_users)),
                         KeyValueItem('bots', Code(bot_accounts)),
                         KeyValueItem('deleted_accounts', Code(deleted_accounts)))

    data = []
    data += [KeyValueItem(key, Code(value)) for key, value in tags.named_tags.items()]
    tags = Section('Tags:', *data or [Italic('None')])
    return KanTeXDocument(chat_info, user_stats, tags)
