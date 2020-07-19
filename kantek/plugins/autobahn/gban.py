"""Plugin to handle global bans"""
import asyncio
import datetime
import logging
from typing import Dict, Optional, List

from telethon.errors import UserNotParticipantError
from telethon.tl.custom import Message
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import Channel, InputReportReasonSpam, InputPeerChannel

from utils import helpers
from utils.client import KantekClient
from utils.mdtex import MDTeXDocument, Section, KeyValueItem, Bold, Code
from utils.pluginmgr import k, Command
from utils.tagmgr import TagManager

tlog = logging.getLogger('kantek-channel-log')

DEFAULT_REASON = 'spam[gban]'
CHUNK_SIZE = 10


@k.command('gban')
async def gban(client: KantekClient, tags: TagManager, chat: Channel, msg: Message,
               args: List, kwargs: Dict, event: Command) -> None:
    """Command to globally ban a user."""
    _gban = tags.get('gban')

    only_joinspam = kwargs.get('only_joinspam', False) or kwargs.get('oj', False)

    verbose = False
    if _gban == 'verbose' or event.is_private:
        verbose = True
    await msg.delete()
    if msg.is_reply:

        bancmd = tags.get('gbancmd')
        reply_msg: Message = await msg.get_reply_message()
        uid = reply_msg.from_id
        if args:
            ban_reason = args[0]
        else:
            ban_reason = DEFAULT_REASON
            try:
                participant = await client(GetParticipantRequest(event.chat_id, reply_msg.from_id))
                join_date = participant.participant.date

                now = datetime.datetime.now(tz=join_date.tzinfo)
                if (now - datetime.timedelta(hours=1)) < join_date:
                    ban_reason = 'joinspam'
                elif only_joinspam:
                    return
            except UserNotParticipantError:
                pass

        message = await helpers.textify_message(reply_msg)
        await client.gban(uid, ban_reason, message)
        peer_channel: InputPeerChannel = await event.get_input_chat()
        await client(ReportRequest(peer_channel, [reply_msg.id], InputReportReasonSpam()))
        if chat.creator or chat.admin_rights:
            if bancmd == 'manual' or bancmd is None:
                await client.ban(chat, uid)
            elif bancmd is not None:
                await reply_msg.reply(f'{bancmd} {ban_reason}')
                await asyncio.sleep(0.5)
            await reply_msg.delete()
    else:
        uids = []
        ban_reason = []
        for arg in args:
            if isinstance(arg, int):
                uids.append(arg)
            else:
                ban_reason.append(arg)
        if ban_reason:
            ban_reason = ' '.join(ban_reason)
        else:
            ban_reason = kwargs.get('reason', DEFAULT_REASON)

        message = kwargs.get('msg')
        if not message:
            link = kwargs.get('link')
            if link:
                try:
                    linked_msg: Message = await helpers.get_linked_message(client, link)
                    message = await helpers.textify_message(linked_msg)
                except Exception:
                    message = link

        skipped_uids = {}
        banned_uids = {}
        progress_message: Optional[Message]
        if verbose and len(uids) > 10:
            progress_message: Message = await client.send_message(chat, f"Processing {len(uids)} User IDs")
        else:
            progress_message = None
        while uids:
            uid_batch = uids[:CHUNK_SIZE]
            for uid in uid_batch:
                banned, reason = await client.gban(uid, ban_reason, message)
                if not banned:
                    skipped_uids[reason] = skipped_uids.get(reason, []) + [str(uid)]
                # sleep to avoid flooding the bots too much
                else:
                    banned_uids[reason] = banned_uids.get(reason, []) + [str(uid)]
                await asyncio.sleep(0.5)
            uids = uids[CHUNK_SIZE:]
            if uids:
                if progress_message:
                    await progress_message.edit(
                        f"Sleeping for 10 seconds after banning {len(uid_batch)} Users. {len(uids)} Users left.")
                await asyncio.sleep(10)

        if progress_message:
            await progress_message.delete()

        if verbose:
            sections = []
            if banned_uids:
                bans = _build_message(banned_uids, message)
                sections.append(Section(Bold(f'GBanned User{"s" if len(banned_uids) > 1 else ""}'), *bans))
            if skipped_uids:
                bans = _build_message(skipped_uids)
                sections.append(Section(Bold('Skipped GBan'), *bans))

            await client.respond(event, MDTeXDocument(*sections))


def _build_message(bans: Dict[str, List[str]], message: Optional[str]) -> List[KeyValueItem]:
    sections = []
    for reason, uids in bans.items():
        sections.append(KeyValueItem(Bold('Reason'), reason))
        sections.append(KeyValueItem(Bold('IDs'), Code(', '.join(uids))))
        if message:
            sections.append(KeyValueItem(Bold('Message'), 'Attached'))
    return sections


@k.command('ungban')
async def ungban(client: KantekClient, msg: Message,
                 args: List, event: Command) -> None:
    """Command to globally unban a user."""
    await msg.delete()

    users_to_unban = [*args]
    if msg.is_reply:
        reply_msg: Message = await msg.get_reply_message()
        uid = reply_msg.from_id
        users_to_unban.append(uid)

    unbanned_users = []
    for uid in users_to_unban:
        if client.db.banlist.get_user(uid):
            await client.ungban(uid)
            unbanned_users.append(str(uid))
    if unbanned_users:
        await client.respond(event, MDTeXDocument(
            Section(Bold('Un-GBanned Users'),
                    KeyValueItem(Bold('IDs'), Code(', '.join(unbanned_users))))))
