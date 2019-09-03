"""Plugin to test the argument parser"""
import logging
from pprint import pformat

from telethon import events
from telethon.events import NewMessage
from telethon.tl.custom import Message

from config import cmd_prefix
from utils import parsers
from utils.mdtex import Bold, Code, KeyValueItem, MDTeXDocument, Section, SubSection, Pre

__version__ = '0.1.0'

tlog = logging.getLogger('kantek-channel-log')


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}arg'))
async def user_info(event: NewMessage.Event) -> None:
    """Show the raw output of the argument parser

    Args:
        event: The event of the command

    Returns: None

    """
    msg: Message = event.message
    _args = msg.raw_text.split()[1:]
    keyword_args, args = parsers.parse_arguments(' '.join(_args))
    _args = []
    for arg in args:
        _args.append(SubSection(Code(arg),
                                KeyValueItem('type', Code(type(arg).__name__))))
    kwargs = []
    for k, v in keyword_args.items():
        kwargs.append(SubSection(Code(k),
                                 KeyValueItem('value', Code(v)),
                                 KeyValueItem('type', Code(type(v).__name__))))
    doc = MDTeXDocument(
        Section(Bold('Args'), *_args),
        Section(Bold('Keyword Args'), *kwargs),
        Section(Bold('Raw'),
                KeyValueItem('args', Pre(pformat(args, width=30))),
                KeyValueItem('keyword_args', Pre(pformat(keyword_args, width=30))))
    )
    await msg.reply(str(doc))
