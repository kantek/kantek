"""Module containing classes to ease creation of nicely formatted messages.
I called it MDTeX because I'm uncreative and the idea of SubSection and SubSubSection
 was taken from LaTeX
"""
from typing import Union


class FormattedBase:
    """Base class for any message type."""
    text: str

    def __add__(self, other):
        return str(self) + str(other)

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.text})'

    def __str__(self) -> str:
        return self.text



String = Union[str, FormattedBase]


class Bold(FormattedBase):
    """A bold text."""

    def __init__(self, text: Union[str, int]) -> None:
        self.text = f'**{text}**'


class Italic(FormattedBase):
    """A italic text."""

    def __init__(self, text: Union[str, int]) -> None:
        self.text = f'__{text}__'


class Code(FormattedBase):
    """A Monospaced text."""

    def __init__(self, text: Union[str, int]) -> None:
        self.text = f'`{text}`'


class Pre(FormattedBase):
    """A Multiline Monospaced text."""

    def __init__(self, text: Union[str, int]) -> None:
        self.text = f'```{text}```'


class Link(FormattedBase):
    """A Hyperlink with a label."""

    def __init__(self, label: String, url: str) -> None:
        self.text = f'[{label}]({url})'


class KeyValueItem(FormattedBase):
    """A item that has a key and a value divided by a colon."""

    def __init__(self, key: String, value: String) -> None:
        self.key = key
        self.value = value
        self.text = f'{key}: {value}'


class Item(FormattedBase):
    """A simple item without any formatting."""

    def __init__(self, text: Union[str, int]) -> None:
        self.text = str(text)


class Section:
    """A section header"""

    def __init__(self, *args: Union[String, 'Section'], indent: int = 4) -> None:
        self.header = args[0]
        self.items = args[1:]
        self.indent = indent

    def __add__(self, other):
        return str(self) + '\n\n' + str(other)

    def __str__(self) -> str:
        return '\n'.join([str(self.header)]
                         + [' ' * self.indent + str(item) for item in self.items])


class SubSection(Section):
    """A subsection Header"""

    def __init__(self, *args: Union[String, Section], indent: int = 8) -> None:
        super().__init__(*args, indent=indent)


class SubSubSection(Section):
    """A subsubsection Header"""

    def __init__(self, *args: Union[String, Section], indent: int = 12) -> None:
        super().__init__(*args, indent=indent)
