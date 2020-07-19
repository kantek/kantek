"""Plugin to test the argument parser"""
import logging
from pprint import pformat
from typing import Dict, List

from telethon.tl.custom import Message

from utils.mdtex import Bold, Code, KeyValueItem, MDTeXDocument, Section, SubSection, Pre
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.command('arg')
async def show_args(msg: Message, args: List, kwargs: Dict) -> None:
    """Show the raw output of the argument parser

    Returns: None

    """
    _args = msg.raw_text.split()[1:]
    _args = []
    for arg in args:
        _args.append(SubSection(Code(arg),
                                KeyValueItem('type', Code(type(arg).__name__))))
    keyword_args = []
    for k, v in kwargs.items():
        keyword_args.append(SubSection(Code(k),
                                       KeyValueItem('value', Code(v)),
                                       KeyValueItem('type', Code(type(v).__name__))))
    doc = MDTeXDocument(
        Section(Bold('Args'), *_args),
        Section(Bold('Keyword Args'), *keyword_args),
        Section(Bold('Raw'),
                KeyValueItem('args', Pre(pformat(args, width=30))),
                KeyValueItem('keyword_args', Pre(pformat(kwargs, width=30))))
    )
    await msg.reply(str(doc))
