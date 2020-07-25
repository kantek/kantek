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
