"""Plugin to test the argument parser"""
import logging
from pprint import pformat
from typing import Dict, List

from telethon.tl.custom import Message

from utils.mdtex import *
from utils.pluginmgr import k

tlog = logging.getLogger('kantek-channel-log')


@k.command('arg')
async def show_args(msg: Message, args: List, kwargs: Dict) -> MDTeXDocument:
    """Show the raw output of the argument parser

    Returns: None

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
