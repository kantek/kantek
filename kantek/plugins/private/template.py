from typing import Optional

from kantex.md import *
from telethon.tl.custom import Message

from database.database import Database
from utils.errors import MissingArgumentsError
from utils.pluginmgr import k

QUERY_MAX_LENGTH = 20


@k.command('template', 't')
async def template(args, db: Database, event, msg: Message) -> Optional[KanTeXDocument]:
    """Edit the command with the templates content

    Arguments:
        `name`: The template name

    """
    if not args:
        await event.delete()
        return

    _template = await db.templates.get(args[0])
    if _template:
        await msg.edit(_template.content)
    else:
        await event.delete()


@template.subcommand()
async def add(args, db: Database) -> KanTeXDocument:
    """Add a template

    Arguments:
        `name`: Name of the template
        `content`: Content of the template

    Examples:
        {cmd} test testcontent
    """
    if len(args) < 2:
        raise MissingArgumentsError(f'Missing {Code("name")} and {Code("content")}')
    name, content = args[0], args[1:]
    content = ' '.join(content)
    existing = await db.templates.get(name)
    await db.templates.add(name, content)
    return KanTeXDocument(
        Section(f'Template {"update" if existing else "created"}',
                KeyValueItem('name', Code(name)),
                KeyValueItem('content', Code(content))))


@template.subcommand()
async def del_(args, db: Database) -> KanTeXDocument:
    """Delete the specified template names

    Arguments:
        `names`: List of template names to delete
    """
    for name in args:
        await db.templates.delete(name)
    return KanTeXDocument(Section('Templates deleted', Code(', '.join(args))))


@template.subcommand()
async def query(db: Database) -> KanTeXDocument:
    """List all templates

    Examples:
        {cmd}
    """
    templates = await db.templates.get_all()
    return KanTeXDocument(
        Section('Templates',
                *[KeyValueItem(t.name, Code(f'{t.content[:QUERY_MAX_LENGTH]}'
                                            f'{"..." if len(t.content) > QUERY_MAX_LENGTH else ""}')) for t in templates]))
