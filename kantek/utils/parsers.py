import re
from typing import Pattern, Dict, List


def parse_tag_syntax(cmd):
    """Parse the syntax for adding tags"""
    NAMED_ATTRIBUTE: Pattern = re.compile(
        r'(\w+):\s?(\[.+?\]|".+"|\w+)')
    named_attrs = re.findall(NAMED_ATTRIBUTE, cmd)
    named_attrs: Dict[str, List[str]] = {name: re.sub(r'[\[\]\"]', '', value).split(',')
                                         for name, value in named_attrs}
    cmd = re.sub(NAMED_ATTRIBUTE, '', cmd)
    attrs = re.findall(r'\w+', cmd)
    return named_attrs, attrs
