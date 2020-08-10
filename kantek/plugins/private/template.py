from typing import Optional

from telethon.tl.custom import Message

from database.database import Database
from utils.mdtex import *
from utils.pluginmgr import k

QUERY_MAX_LENGTH = 20


@k.command('template', 't')
async def template(args, db: Database, event, msg: Message) -> Optional[MDTeXDocument]:
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
async def add(args, db: Database) -> MDTeXDocument:
    """Add a template

    Arguments:
        `name`: Name of the template
        `content`: Content of the template

    Examples:
        {cmd} test testcontent
    """
    if len(args) < 2:
        return MDTeXDocument(Section('Error', Italic('Missing arguments.')))
    name, content = args[:2]
    existing = await db.templates.get(args[0])
    await db.templates.add(name, content)
    return MDTeXDocument(
        Section(f'Template {"update" if existing else "created"}',
                KeyValueItem('name', Code(name)),
                KeyValueItem('content', Code(content))))


@template.subcommand()
async def del_(args, db: Database) -> MDTeXDocument:
    """Delete the specified template names

    Arguments:
        `names`: List of template names to delete
    """
    for name in args:
        await db.templates.delete(name)
    return MDTeXDocument(Section('Templates deleted', Code(', '.join(args))))


@template.subcommand()
async def query(db: Database) -> MDTeXDocument:
    """List all templates

    Examples:
        {cmd}
    """
    templates = await db.templates.get_all()
    return MDTeXDocument(
        Section('Templates',
                *[KeyValueItem(t.name, Code(f'{t.content[:QUERY_MAX_LENGTH]}'
                                            f'{"..." if len(t.content) > QUERY_MAX_LENGTH else ""}')) for t in templates]))
