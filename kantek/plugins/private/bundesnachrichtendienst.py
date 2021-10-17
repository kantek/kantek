import re
from typing import Dict, List

from kantex.md import *
from telethon import events
from telethon.events import NewMessage

from kantek import Client, Database
from kantek import Command
from kantek.utils.pluginmgr import k


@k.event(events.NewMessage(incoming=True))
async def bundesnachrichtendienst_event(event: NewMessage.Event) -> None:
    if event.is_private:
        return

    client: Client = event.client
    items = await client.db.bundesnachrichtendienst.get_all_for_chat(event.chat_id)
    if not items:
        return
    text = event.message.text
    for item in items:
        if item.pattern:
            if re.match(item.pattern, text, re.I):
                await handle_event(event, item.action)
                return


async def handle_event(event: NewMessage.Event, action: str) -> None:
    client: Client = event.client

    if action == 'delete':
        await event.delete()
    elif action == 'kick':
        await client.kick_participant(event.chat_id, event.message.sender_id)
    elif action == 'ban':
        await client.ban(event.chat_id, event.message.sender_id)


@k.command('bundesnachrichtendienst', 'bnd')
async def bundesnachrichtendienst(db: Database, event: Command) -> KanTeXDocument:
    """"Perform an action on a message matching a regex/character class

    Arguments:
        `arg`: Args

    Examples:
        {cmd}
    """
    items = await db.bundesnachrichtendienst.get_all_for_chat(event.chat_id)
    if not items:
        return KanTeXDocument(Section('Bundesnachrichtendienst', Italic('None')))
    else:
        rows = []
        for item in items:
            rows.append(
                SubSubSection(
                    Code(item.id),
                    KeyValueItem('action', Code(item.action)),
                    KeyValueItem('pattern', Code(item.pattern)) if item.pattern else '',
                    KeyValueItem('class', Code(item.character_class)) if item.character_class else '',
                )
            )
        return KanTeXDocument(Section('Bundesnachrichtendienst', *rows))


@bundesnachrichtendienst.subcommand()
async def add(db: Database, kwargs: Dict, event: Command) -> KanTeXDocument:
    """Add a pattern to the BND

    Arguments:
        `action`: The action to do on a match, can be `delete`, `kick`, `ban`
        `pattern`: Regex to match
        `class`: Unused

    Examples:
        {cmd} pattern: "^(hello|hi+|salom|hey)$" action: delete
    """
    action = kwargs.get('action')
    pattern = kwargs.get('pattern').strip()
    character_class = kwargs.get('class')

    if not action:
        return KanTeXDocument(Section('TypeError', f'missing required keyword argument: {Code(action)}'))
    if not pattern and not character_class:
        return KanTeXDocument(
            Section('TypeError', f'missing required keyword argument: {Code("pattern")} or {Code("class")}'))

    try:
        re.compile(pattern)
    except re.error as e:
        return KanTeXDocument(
            Section('Pattern Errror',
                    Code(e.pattern),
                    Code('^'.rjust(e.colno)),
                    Code(e.msg)))

    item = await db.bundesnachrichtendienst.add(event.chat_id, action, pattern, character_class)
    return KanTeXDocument(
        Section('Item', KeyValueItem('id', Code(item.id)),
                KeyValueItem('action', Code(item.action)),
                KeyValueItem('pattern', Code(item.pattern)) if item.pattern else '',
                KeyValueItem('class', Code(item.character_class)) if item.character_class else '', )
    )


@bundesnachrichtendienst.subcommand()
async def edit(db: Database, kwargs: Dict, args: List, event: Command) -> KanTeXDocument:
    """Update a entry

    Arguments:
        `uid`: The id of the entry
        `action`: The action to do on a match, can be `delete`, `kick`, `ban`
        `pattern`: Regex to match
        `class`: Unused

    Examples:
        {cmd} 6 action: kick pattern: def
    """
    uid = args[0]
    item = await db.bundesnachrichtendienst.get(uid)
    action = kwargs.get('action', item.action)
    pattern = kwargs.get('pattern', item.pattern)
    character_class = kwargs.get('class', item.character_class)

    item = await db.bundesnachrichtendienst.edit(uid, action, pattern, character_class)

    return KanTeXDocument(
        Section('Updated Item', KeyValueItem('id', Code(item.id)),
                KeyValueItem('action', Code(item.action)),
                KeyValueItem('pattern', Code(item.pattern)) if item.pattern else '',
                KeyValueItem('class', Code(item.character_class)) if item.character_class else '', ))


@bundesnachrichtendienst.subcommand()
async def del_(db: Database, args: List) -> KanTeXDocument:
    """"Remove a pattern from the BND

        Arguments:
            `uids`: The ids to delete

        Examples:
            {cmd} 1 2 3
        """
    for uid in args:
        await db.bundesnachrichtendienst.remove(uid)

    return KanTeXDocument(Section('Removed', Code(', '.join(map(str, args)))))
