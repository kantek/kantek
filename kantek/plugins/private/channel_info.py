"""Plugin to get information about a channel."""
from telethon import events
from telethon.events import NewMessage
from telethon.tl.types import Channel

__version__ = '0.1.0'
__commands__ = ['info']


@events.register(events.NewMessage(outgoing=True, pattern=r'!!info'))
async def channel_info(event: NewMessage.Event) -> None:
    """Show the id of the group.

    Args:
        event: The event with the command

    Returns: None

    """
    chat: Channel = event.chat

    await event.respond(f'{chat.title} `{chat.id}`',
                        reply_to=event.reply_to_msg_id)
