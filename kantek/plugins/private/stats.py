"""Plugin to get statistics of the user account"""
import logging
import time

from telethon import events
from telethon.events import NewMessage
from telethon.tl.custom import Dialog
from telethon.tl.types import Channel, Chat, User

from config import cmd_prefix
from utils import helpers
from utils.client import KantekClient
from utils.mdtex import Bold, Italic, KeyValueItem, MDTeXDocument, Section, SubSection

__version__ = '0.1.1'

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}stats'))
async def stats(event: NewMessage.Event) -> None:  # pylint: disable = R0912, R0914, R0915
    """Command to get stats about the account"""
    client: KantekClient = event.client
    waiting_message = await client.respond(event, 'Collecting stats. This might take a while.')
    start_time = time.time()
    private_chats = 0
    bots = 0
    groups = 0
    broadcast_channels = 0
    admin_in_groups = 0
    creator_in_groups = 0
    admin_in_broadcast_channels = 0
    creator_in_channels = 0
    unread_mentions = 0
    unread = 0
    largest_group_member_count = 0
    largest_group_with_admin = 0
    dialog: Dialog
    async for dialog in client.iter_dialogs():
        entity = dialog.entity

        if isinstance(entity, Channel):
            # participants_count = (await client.get_participants(dialog, limit=0)).total
            if entity.broadcast:
                broadcast_channels += 1
                if entity.creator or entity.admin_rights:
                    admin_in_broadcast_channels += 1
                if entity.creator:
                    creator_in_channels += 1

            elif entity.megagroup:
                groups += 1
                # if participants_count > largest_group_member_count:
                #     largest_group_member_count = participants_count
                if entity.creator or entity.admin_rights:
                #     if participants_count > largest_group_with_admin:
                #         largest_group_with_admin = participants_count
                    admin_in_groups += 1
                if entity.creator:
                    creator_in_groups += 1

        elif isinstance(entity, User):
            private_chats += 1
            if entity.bot:
                bots += 1

        elif isinstance(entity, Chat):
            groups += 1
            if entity.creator or entity.admin_rights:
                admin_in_groups += 1
            if entity.creator:
                creator_in_groups += 1

        unread_mentions += dialog.unread_mentions_count
        unread += dialog.unread_count
    stop_time = time.time() - start_time

    full_name = await helpers.get_full_name(await client.get_me())
    response = MDTeXDocument(Section(
        Bold(f'Stats for {full_name}'),
        SubSection(
            KeyValueItem(Bold('Private Chats'), private_chats),
            KeyValueItem(Bold('Users'), private_chats - bots),
            KeyValueItem(Bold('Bots'), bots)),
        KeyValueItem(Bold('Groups'), groups),
        KeyValueItem(Bold('Channels'), broadcast_channels),
        SubSection(
            KeyValueItem(Bold('Admin in Groups'), admin_in_groups),
            KeyValueItem(Bold('Creator'), creator_in_groups),
            KeyValueItem(Bold('Admin Rights'), admin_in_groups - creator_in_groups)),
        SubSection(
            KeyValueItem(Bold('Admin in Channels'), admin_in_broadcast_channels),
            KeyValueItem(Bold('Creator'), creator_in_channels),
            KeyValueItem(Bold('Admin Rights'), admin_in_broadcast_channels - creator_in_channels)),
        KeyValueItem(Bold('Unread'), unread),
        KeyValueItem(Bold('Unread Mentions'), unread_mentions)),
        # KeyValueItem(Bold('Largest Group'), largest_group_member_count),
        # KeyValueItem(Bold('Largest Group with Admin'), largest_group_with_admin)),
        Italic(f'Took {stop_time:.02f}s'))

    await client.respond(event, response, reply=False)
    await waiting_message.delete()
    tlog.info('Ran `stats` in `%s`. Response:\n %s', event.chat.title, response)
