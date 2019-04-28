"""Module containing regex parsers for different occasions."""
import re
from typing import Dict, List, Pattern, Tuple

NAMED_ATTRIBUTE: Pattern = re.compile(r'(\w+):\s?(\[.+?\]|\".+\"|\w+)')


def parse_arguments(arguments: str) -> Tuple[Dict[str, str], List[str]]:
    """Parse arguments provided as string

    >>> parse_arguments('arg1 arg2 arg3')
    ({}, ['arg1', 'arg2', 'arg3'])

    >>> parse_arguments('arg1: val1 arg2: "val2.1 val2.2"')
    ({'arg1': 'val1', 'arg2': 'val2.1 val2.2'}, [])

    >>> parse_arguments('arg1: val1 arg2 arg3: "val3.1 val3.2" arg3')
    ({'arg1': 'val1', 'arg3': 'val3.1 val3.2'}, ['arg2', 'arg3'])

    >>> parse_arguments('arg1: val1.1 val1.2')
    ({'arg1': 'val1'}, ['1', 'val1', '2'])

    >>> parse_arguments('arg1: "val1.2"')
    ({'arg1': 'val1.2'}, [])

    >>> parse_arguments('"val1.2"')
    ({}, ['val1.2'])

    Args:
        arguments: The string with the arguments that should be parsed

    Returns:
        A Tuple with keyword and positional arguments

    """

    _named_attrs = re.findall(NAMED_ATTRIBUTE, arguments)
    keyword_args: Dict[str, str] = {name: re.sub(r'[\[\]\"]', '', value)
                                   for name, value in _named_attrs}
    arguments = re.sub(NAMED_ATTRIBUTE, '', arguments)
    args = re.findall(r'\w+', arguments)
    return keyword_args, args
