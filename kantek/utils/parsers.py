"""Module containing regex parsers for different occasions."""
import re
from typing import Dict, List, Pattern, Tuple

NAMED_ATTRIBUTE: Pattern = re.compile(r'(\w+):\s?(\[.+?\]|".+"|\w+)')


def parse_arguments(cmd: str) -> Tuple[Dict[str, str], List[str]]:
    """Parse the syntax for adding tags"""

    _named_attrs = re.findall(NAMED_ATTRIBUTE, cmd)
    named_attrs: Dict[str, str] = {name: re.sub(r'[\[\]\"]', '', value)
                                   for name, value in _named_attrs}
    cmd = re.sub(NAMED_ATTRIBUTE, '', cmd)
    attrs = re.findall(r'\w+', cmd)
    return named_attrs, attrs
