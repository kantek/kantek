"""Module containing regex parsers for different occasions."""
import re
from typing import Dict, List, Pattern, Tuple, Union

KEYWORD_ARGUMENT: Pattern = re.compile(r'(\S+):\s?(\[.+?\]|\".+\"|[\w-]\S*)')
FLAG_ARGUMENT: Pattern = re.compile(r'(?:\s|^)-\w+')
QUOTED_ARGUMENT: Pattern = re.compile(r'(?:\")(.*?)(?:\")')
RANGE_PATTERN: Pattern = re.compile(r'-?\d+\.\.-?\d+')
BOOL_MAP = {
    'false': False,
    'true': True,
}

Value = Union[int, str, float, complex, bool]
KeywordArgument = Union[Value, range, List[Value]]

EXPR_PATTERN: Pattern = re.compile(r'(?P<duration>\d+)(?P<unit>[smhdw])')

MULTIPLICATION_MAP = {
    's': 1,
    'm': 60,
    'h': 60 * 60,
    'd': 60 * 60 * 24,
    'w': 60 * 60 * 24 * 7,
}


def _parse_number(val: str) -> Value:
    if val.isdecimal():
        return int(val)

    try:
        return float(val)
    except ValueError:
        pass

    try:
        # replace i with j since i is more common for imaginary numbers but python wants j
        return complex(val.replace('i', 'j'))
    except ValueError:
        pass
    return val


def parse_arguments(arguments: str) -> Tuple[Dict[str, KeywordArgument], List[Value]]:
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

    >>> parse_arguments('arg: 123 456 arg2: True')
    ({'arg': 123, 'arg2': True}, [456])

    >>> parse_arguments('arg: [123, 456] arg2: ["abc", "de f", "xyz"]')
    ({'arg': [123, 456], 'arg2': ['abc', 'de f', 'xyz']}, [])

    >>> parse_arguments('arg: 1..10 arg2: -5..5 arg2: -10..0')
    ({'arg': range(1, 10), 'arg2': range(-10, 0)}, [])

    >>> parse_arguments('1.24124 2151.2352 23626.325')
    ({}, [1.24124, 2151.2352, 23626.325])

    >>> parse_arguments('1e4 2.5e4 125e-5')
    ({}, [10000.0, 25000.0, 0.00125])

    >>> parse_arguments('3+3j 4+2i')
    ({}, [(3+3j), (4+2j)])

    >>> parse_arguments('https://example.com')
    ({}, ['https://example.com'])

    >>> parse_arguments('keyword: "Something[not a list]"')
    ({'keyword': 'Something[not a list]'}, [])

    >>> parse_arguments('keyword: 1 keyword2: 5')
    ({'keyword': 1, 'keyword2': 5}, [])

    >>> parse_arguments('posarg -flag')
    ({'flag': True}, ['posarg'])

    >>> parse_arguments('-flag')
    ({'flag': True}, [])

    >>> parse_arguments('posarg -flag 125e-5')
    ({'flag': True}, ['posarg', 0.00125])

    Args:
        arguments: The string with the arguments that should be parsed

    Returns:
        A Tuple with keyword and positional arguments

    """

    _named_attrs = re.findall(KEYWORD_ARGUMENT, arguments)
    keyword_args: Dict[str, KeywordArgument] = {}
    for name, value in _named_attrs:
        if value.startswith('"') and value.endswith('"'):
            keyword_args.update({name: re.sub(r'\"', '', value)})
            continue

        val = re.sub(r'\"', '', value)
        val = _parse_number(val)
        if isinstance(val, str):
            if re.search(r'\[.*\]', val):
                val = re.sub(r'[\[\]]', '', val).split(',')
                val = [_parse_number(v.strip()) for v in val]
            elif re.search(RANGE_PATTERN, val):
                start, stop = val.split('..')
                val = range(int(start), int(stop))
            else:
                val = BOOL_MAP.get(val.lower(), val)
        keyword_args.update({name: val})

    arguments = re.sub(KEYWORD_ARGUMENT, '', arguments)

    flag_args = re.findall(FLAG_ARGUMENT, arguments)
    for flag in flag_args:
        keyword_args[flag.strip()[1:]] = True
    arguments = re.sub(FLAG_ARGUMENT, '', arguments)

    quoted_args = re.findall(QUOTED_ARGUMENT, arguments)
    arguments = re.sub(QUOTED_ARGUMENT, '', arguments)
    # convert any numbers to int
    args = [_parse_number(val) for val in arguments.split()]
    return keyword_args, args + quoted_args


def parse_time(expr) -> int:
    """Parse a abbreviated time expression into seconds

    Supports s, m, h, d and w for seconds, minutes, hours, days and weeks respectively.

    >>> parse_time('1s')
    1

    >>> parse_time('1m')
    60

    >>> parse_time('1h')
    3600

    >>> parse_time('1d')
    86400

    >>> parse_time('1w')
    604800

    >>> parse_time('1s2m')
    121

    >>> parse_time('3h1d')
    97200

    Args:
        expr: The time expression

    Returns: The time in seconds
    """
    total_duration = 0
    for duration, unit in EXPR_PATTERN.findall(expr):
        total_duration += int(duration) * MULTIPLICATION_MAP[unit]
    return total_duration
