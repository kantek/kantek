"""Module containing regex parsers for different occasions."""
import ast
import re
from typing import Dict, List, Pattern, Tuple, Union

KEYWORD_ARGUMENT: Pattern = re.compile(r'(\S+):\s?(\[.+?\]|\".+\"|[\w\-\.]\S*)', re.DOTALL)
FLAG_ARGUMENT: Pattern = re.compile(r'(?:\s|^)-\D(?:\w+)?')
QUOTED_ARGUMENT: Pattern = re.compile(r'(?:\")(.*?)(?:\")', re.DOTALL)
RANGE_PATTERN: Pattern = re.compile(r'(?P<start>-?\d+)?\.\.(?P<end>-?\d+)?')
BOOL_MAP = {
    'false': False,
    'true': True,
}

Value = Union[int, str, float, complex, bool, range, List['Value']]
KeywordArgument = Union[Value, range, List[Value]]

EXPR_PATTERN: Pattern = re.compile(r'(?P<duration>\d+)(?P<unit>[smhdw])')

MULTIPLICATION_MAP = {
    's': 1,
    'm': 60,
    'h': 60 * 60,
    'd': 60 * 60 * 24,
    'w': 60 * 60 * 24 * 7,
}


def _parse_types(val: str) -> Value:
    try:
        return ast.literal_eval(val)
    except (ValueError, SyntaxError):
        pass

    try:
        # replace i with j since i is more common for imaginary numbers but python wants j
        return complex(val.replace('i', 'j'))
    except ValueError:
        pass

    if re.search(r'\[.*\]', val):
        val = re.sub(r'[\[\]]', '', val).split(',')
        return [_parse_types(v.strip()) for v in val]
    elif match := re.search(RANGE_PATTERN, val):
        end = int(match.group('end'))
        if start := match.group('start'):
            return range(int(start), end)
        else:
            return range(end)
    else:
        return BOOL_MAP.get(val.lower(), val)


def arguments(args: str) -> Tuple[Dict[str, KeywordArgument], List[Value]]:
    """Parse arguments provided as string

    >>> arguments('arg1 arg2 arg3')
    ({}, ['arg1', 'arg2', 'arg3'])

    >>> arguments('arg1: val1 arg2: "val2.1 val2.2"')
    ({'arg1': 'val1', 'arg2': 'val2.1 val2.2'}, [])

    >>> arguments('arg1: val1 arg2 arg3: "val3.1 val3.2" arg3')
    ({'arg1': 'val1', 'arg3': 'val3.1 val3.2'}, ['arg2', 'arg3'])

    >>> arguments('arg1: "val1.1" val1.2')
    ({'arg1': 'val1.1'}, ['val1.2'])

    >>> arguments('arg1: "val1.2"')
    ({'arg1': 'val1.2'}, [])

    >>> arguments('"val space"')
    ({}, ['val space'])

    >>> arguments('@username')
    ({}, ['@username'])

    >>> arguments('arg: True arg2: false')
    ({'arg': True, 'arg2': False}, [])

    >>> arguments('arg: 123 456 arg2: True')
    ({'arg': 123, 'arg2': True}, [456])

    >>> arguments('arg: [123, 456] arg2: ["abc", "de f", "xyz"]')
    ({'arg': [123, 456], 'arg2': ['abc', 'de f', 'xyz']}, [])

    >>> arguments('arg: 1..10 arg2: -5..5 arg2: -10..0')
    ({'arg': range(1, 10), 'arg2': range(-10, 0)}, [])

    >>> arguments('1.24124 2151.2352 23626.325')
    ({}, [1.24124, 2151.2352, 23626.325])

    >>> arguments('1e4 2.5e4 125e-5')
    ({}, [10000.0, 25000.0, 0.00125])

    >>> arguments('3+3j 4+2i')
    ({}, [(3+3j), (4+2j)])

    >>> arguments('https://example.com')
    ({}, ['https://example.com'])

    >>> arguments('keyword: "Something[not a list]"')
    ({'keyword': 'Something[not a list]'}, [])

    >>> arguments('keyword: 1 keyword2: 5')
    ({'keyword': 1, 'keyword2': 5}, [])

    >>> arguments('posarg -flag')
    ({'flag': True}, ['posarg'])

    >>> arguments('-flag')
    ({'flag': True}, [])

    >>> arguments('-1001129887931')
    ({}, [-1001129887931])

    >>> arguments('posarg -flag 125e-5')
    ({'flag': True}, ['posarg', 0.00125])

    >>> arguments('[1,2,3] 1..20')
    ({}, [[1, 2, 3], range(1, 20)])

    >>> arguments('[1..5,6..10]')
    ({}, [[range(1, 5), range(6, 10)]])

    >>> arguments('..20 range: ..20')
    ({'range': range(0, 20)}, [range(0, 20)])

    Args:
        args: The string with the arguments that should be parsed

    Returns:
        A Tuple with keyword and positional arguments

    """

    _named_attrs = re.findall(KEYWORD_ARGUMENT, args)
    keyword_args: Dict[str, KeywordArgument] = {}
    for name, value in _named_attrs:
        if value.startswith('"') and value.endswith('"'):
            keyword_args.update({name: re.sub(r'\"', '', value)})
            continue

        val = re.sub(r'\"', '', value)
        val = _parse_types(val)
        if isinstance(val, str):
            val = _parse_types(val)
        keyword_args.update({name: val})

    args = re.sub(KEYWORD_ARGUMENT, '', args)

    flag_args = re.findall(FLAG_ARGUMENT, args)
    for flag in flag_args:
        keyword_args[flag.strip()[1:]] = True
    args = re.sub(FLAG_ARGUMENT, '', args)

    quoted_args = re.findall(QUOTED_ARGUMENT, args)
    args = re.sub(QUOTED_ARGUMENT, '', args)
    # convert any numbers to int
    args = [_parse_types(val) for val in args.split()]
    return keyword_args, args + quoted_args


class MissingExpression(Exception):
    pass


def time(expr) -> int:
    """Parse a abbreviated time expression into seconds

    Supports s, m, h, d and w for seconds, minutes, hours, days and weeks respectively.

    >>> time('1s')
    1

    >>> time('1m')
    60

    >>> time('1h')
    3600

    >>> time('1d')
    86400

    >>> time('1w')
    604800

    >>> time('1s2m')
    121

    >>> time('3h1d')
    97200

    Args:
        expr: The time expression

    Returns: The time in seconds
    """

    total_duration = 0
    if match := EXPR_PATTERN.findall(str(expr)):
        for duration, unit in match:
            total_duration += int(duration) * MULTIPLICATION_MAP[unit]
    else:
        raise MissingExpression('No valid duration expression found.')
    return total_duration
