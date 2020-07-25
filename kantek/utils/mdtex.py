"""Module containing classes to ease creation of nicely formatted messages.
I called it MDTeX because I'm uncreative and the idea of SubSection and SubSubSection
 was taken from LaTeX
"""
from typing import Union, Iterable, TypeVar

K = TypeVar('K')
V = TypeVar('V')


class FormattedBase:
    """Base class for any message type."""
    text: str

    def __add__(self, other: Union[V, 'FormattedBase']) -> str:
        return str(self) + str(other)

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.text})'

    def __str__(self) -> str:
        return self.text


class Bold(FormattedBase):
    """A bold text."""

    def __init__(self, text: V) -> None:
        self.text = f'**{text}**'


class Italic(FormattedBase):
    """A italic text."""

    def __init__(self, text: V) -> None:
        self.text = f'__{text}__'


class Code(FormattedBase):
    """A Monospaced text."""

    def __init__(self, text: V) -> None:
        self.text = f'`{text}`'


class Pre(FormattedBase):
    """A Multiline Monospaced text."""

    def __init__(self, text: V) -> None:
        self.text = f'```{text}```'


class Link(FormattedBase):
    """A Hyperlink with a label."""

    def __init__(self, label: V, url: str) -> None:
        self.text = f'[{label}]({url})'


class Mention(Link):
    """Inline Mention of a User."""

    def __init__(self, label: V, uid: int):
        super().__init__(label, f'tg://user?id={uid}')


class KeyValueItem(FormattedBase):
    """A item that has a key and a value divided by a colon."""

    def __init__(self, key: Union[K, FormattedBase], value: Union[V, FormattedBase]) -> None:
        self.key = key
        self.value = value
        self.text = f'{key}: {value}'


class Item(FormattedBase):
    """A simple item without any formatting."""

    def __init__(self, text: V) -> None:
        self.text = str(text)


class Section:
    """A section header"""

    def __init__(self, *args: Union[V, 'SubSection'], indent: int = 4) -> None:
        self.header = Bold(args[0])
        self.items = [i for i in args[1:] if i]
        self.indent = indent

    def __add__(self, other: Union[V, 'Section']) -> 'MDTeXDocument':
        return MDTeXDocument(self, *other)

    def __str__(self) -> str:
        return '\n'.join([str(self.header)]
                         + [' ' * self.indent + str(item) for item in self.items
                            if item is not None])

    def append(self, item: Union[V, FormattedBase, 'SubSection']) -> None:
        """Append an item to the section"""
        self.items.append(item)

    def extend(self, items: Iterable) -> None:
        """Extend the section with a list of items"""
        self.items.extend(items)


class SubSection(Section):
    """A subsection Header"""

    def __init__(self, *args: Union[V, 'SubSubSection'], indent: int = 8) -> None:
        super().__init__(*args, indent=indent)


class SubSubSection(SubSection):
    """A subsubsection Header"""

    def __init__(self, *args: V, indent: int = 12) -> None:
        super().__init__(*args, indent=indent)


class MDTeXDocument:
    """Document containing sections."""

    def __init__(self, *args: Union[V, 'Section']) -> None:
        self.sections = [i for i in args if i]

    def __str__(self) -> str:
        return '\n\n'.join([str(section) for section in self.sections])


__all__ = ['Bold', 'Italic', 'Code', 'Pre', 'Link', 'Mention', 'KeyValueItem', 'Item',
           'Section', 'SubSection', 'SubSubSection',
           'MDTeXDocument']
