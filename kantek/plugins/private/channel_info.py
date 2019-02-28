from telethon import client, events
from telethon.events import NewMessage
from telethon.tl.patched import Message as PMessage
from telethon.tl.types import Channel

__version__ = '0.1.0'
__commands__ = ['info']

@events.register(events.NewMessage(outgoing=True, pattern=r'!!info'))
async def channel_info(event: NewMessage.Event) -> None:
    """Replace certain keywords in outgoing messages."""
    msg: PMessage = event.message
    chat: Channel = event.chat
    # elif chat.admin_rights:
    await event.respond(f'{chat.title} `{chat.id}`',
                        reply_to=event.reply_to_msg_id)
