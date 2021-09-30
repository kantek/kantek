from dataclasses import dataclass, field
from typing import Dict


@dataclass
class BlacklistItem:
    index: int
    value: str
    retired: bool


@dataclass
class Chat:
    id: int
    tags: Dict[str, str]
    permissions: Dict[str, bool] = field(default_factory=lambda: {})
    locked: bool = False


@dataclass
class BannedUser:
    id: int
    reason: str


@dataclass
class Template:
    name: str
    content: str
    edit: bool
