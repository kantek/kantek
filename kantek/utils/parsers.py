"""Module containing regex parsers for different occasions."""
import re
from typing import Dict, List, Pattern, Tuple

KEYWORD_ARGUMENT: Pattern = re.compile(r'(\w+):\s?(\[.+?\]|\".+\"|\w+)')
QUOTED_ARGUMENT: Pattern = re.compile(r'(?:\")(.*?)(?:\")')
BOOL_MAP = {
    'false': False,
    'False': False,
    'true': True,
    'True': True
}


def parse_arguments(arguments: str) -> Tuple[Dict[str, str], List[str]]:
    """Parse arguments provided as string

    >>> parse_arguments('arg1 arg2 arg3')
    ({}, ['arg1', 'arg2', 'arg3'])

    >>> parse_arguments('arg1: val1 arg2: "val2.1 val2.2"')
    ({'arg1': 'val1', 'arg2': 'val2.1 val2.2'}, [])

    >>> parse_arguments('arg1: val1 arg2 arg3: "val3.1 val3.2" arg3')
    ({'arg1': 'val1', 'arg3': 'val3.1 val3.2'}, ['arg2', 'arg3'])

    >>> parse_arguments('arg1: "val1.1" val1.2')
    ({'arg1': 'val1.1'}, ['val1.2'])

    >>> parse_arguments('arg1: "val1.2"')
    ({'arg1': 'val1.2'}, [])

    >>> parse_arguments('"val space"')
    ({}, ['val space'])

    >>> parse_arguments('@username')
    ({}, ['@username'])

    >>> parse_arguments('arg: True arg2: false')
    ({'arg': True, 'arg2': False}, [])

    Args:
        arguments: The string with the arguments that should be parsed

    Returns:
        A Tuple with keyword and positional arguments

    """

    _named_attrs = re.findall(KEYWORD_ARGUMENT, arguments)
    keyword_args: Dict[str, str] = {}
    for name, value in _named_attrs:
        _value = re.sub(r'\"', '', value)
        keyword_args.update({name: BOOL_MAP.get(_value, _value)})

    arguments = re.sub(KEYWORD_ARGUMENT, '', arguments)
    quoted_args = re.findall(QUOTED_ARGUMENT, arguments)
    arguments = re.sub(QUOTED_ARGUMENT, '', arguments)
    args = arguments.split()
    return keyword_args, args + quoted_args
