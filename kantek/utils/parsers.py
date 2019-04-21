"""Module containing regex parsers for different occasions."""
import re
from typing import Pattern, Dict, List, Tuple


def parse_tag_syntax(cmd: str) -> Tuple[Dict[str, List[str]], List[str]]:
    """Parse the syntax for adding tags"""
    NAMED_ATTRIBUTE: Pattern = re.compile(
        r'(\w+):\s?(\[.+?\]|".+"|\w+)')
    _named_attrs = re.findall(NAMED_ATTRIBUTE, cmd)
    named_attrs: Dict[str, List[str]] = {name: re.sub(r'[\[\]\"]', '', value).split(',')
                                         for name, value in _named_attrs}
    cmd = re.sub(NAMED_ATTRIBUTE, '', cmd)
    attrs = re.findall(r'\w+', cmd)
    return named_attrs, attrs
