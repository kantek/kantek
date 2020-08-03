from datetime import timedelta
from pprint import pformat
from typing import List, Dict

from telethon.tl.custom import Message
from telethon.tl.functions.messages import MigrateChatRequest

from database.database import Database
from utils import parsers
from utils.client import Client
from utils.mdtex import *
from utils.parsers import MissingExpression
from utils.pluginmgr import k, _Command, _Signature


@k.command('dev', document=False)
async def dev() -> None:
    """Random convenience functions for the bot developers.

    These are unsupported. Don't try to get support for them.
    """
    pass


@dev.subcommand()
async def requires(client: Client, args, kwargs) -> MDTeXDocument:
    """List all commands that require a certain argument to their callbacks.

    Arguments:
        `attribute`: The attribute that should be checked for
        `hide`: Hide command if the attribute is the value. Pass None to show everything. Defaults to False.

    Examples:
        {cmd} db
        {cmd} msg hide: None
        {cmd} client hide: True
    """
    plugins = client.plugin_mgr
    _requires = args[0]
    hide = kwargs.get('hide', False)
    supported_args = _Signature.__annotations__.keys()
    if _requires not in supported_args:
        return MDTeXDocument(
            Section('Error',
                    KeyValueItem('Unsupported argument', Code(_requires)),
                    KeyValueItem('Supported', ', '.join(map(str, map(Code, supported_args))))))
    result = Section('Result')
    cmd: _Command
    for name, cmd in plugins.commands.items():
        req = cmd.signature.__dict__[_requires]
        _cmd = SubSection(name)
        if req is not hide:
            _cmd.append(KeyValueItem(_requires, req))
        if cmd.subcommands:
            for scname, scmd in cmd.subcommands.items():
                screq = scmd.signature.__dict__[_requires]
                if screq is not hide:
                    _scmd = SubSubSection(scname,
                                          KeyValueItem(_requires, screq))
                    _cmd.append(_scmd)
        if _cmd.items:
            result.append(_cmd)
    return MDTeXDocument(result)


@dev.subcommand()
async def args(args: List, kwargs: Dict) -> MDTeXDocument:
    """Show the raw output of the argument parser

    Examples:
        {cmd} arg1 arg2 arg3
        {cmd} arg1: val1 arg2: "val2.1 val2.2"
        {cmd} arg: [123, 456] arg2: ["abc", "de f", "xyz"]
        {cmd} arg: 1..10 arg2: -5..5 arg2: -10..0
        {cmd} 1e4 2.5e4 125e-5
        {cmd} 3+3j 4+2i
        {cmd} keyword: 1 keyword2: 5
        {cmd} posarg -flag
        {cmd} posarg -flag 125e-5

    """
    _args = []
    for arg in args:
        _args.append(SubSection(Code(arg),
                                KeyValueItem('type', Code(type(arg).__name__))))
    keyword_args = []
    for key, value in kwargs.items():
        keyword_args.append(SubSection(Code(key),
                                       KeyValueItem('value', Code(value)),
                                       KeyValueItem('type', Code(type(value).__name__))))
    return MDTeXDocument(
        Section('Args', *_args),
        Section('Keyword Args', *keyword_args),
        Section('Raw',
                KeyValueItem('args', Pre(pformat(args, width=30))),
                KeyValueItem('keyword_args', Pre(pformat(kwargs, width=30))))
    )


@dev.subcommand()
async def time(args: List[str]) -> MDTeXDocument:
    """Parse specified duration expressions into timedeltas
    Arguments:
        `exprs`: Time expressions

    Examples:
        {cmd} 1d
        {cmd} 1h30m 20s1m
        {cmd} 2w3d3h5s
    """
    m = Section('Parsed Durations')
    for arg in args:
        try:
            seconds = parsers.time(arg)
            m.append(
                SubSection(arg,
                           KeyValueItem('seconds', seconds),
                           KeyValueItem('formatted', str(timedelta(seconds=seconds)))))
        except MissingExpression as err:
            m.append(SubSection(arg, Italic(err)))
    return MDTeXDocument(m)


@dev.subcommand()
async def sa(kwargs, db: Database) -> MDTeXDocument:
    """Output the value of a Strafanzeige

    Arguments:
        `sa`: Strafanzeige key

    Examples:
        {cmd} sa: 1ssfG8uYtduwWA
    """
    sa = kwargs.get('sa')
    if value := await db.strafanzeigen.get(sa):
        return MDTeXDocument(Section('Strafanzeige',
                                     KeyValueItem('key', Code(sa)),
                                     KeyValueItem('value', Code(value))))
    else:
        return MDTeXDocument(Section('Strafanzeige', Italic('Key does not exist')))


@dev.subcommand()
async def cat(msg, event, client):
    """Responds with the content of the file that was replied
    This does not check if the message is too large or if the file is text
    """
    if msg.is_reply:  # pylint: disable = R1702
        reply_msg: Message = await msg.get_reply_message()
        data = await reply_msg.download_media(bytes)
        if data:
            await client.respond(event, data.decode())


@dev.subcommand()
async def upgrade(client, chat):
    """Upgrade a normal chat to a supergroup
    """
    await client(MigrateChatRequest(chat.id))
