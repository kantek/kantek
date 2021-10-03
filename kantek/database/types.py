from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


@dataclass
class BlacklistItem:
    index: int
    value: str
    retired: bool


@dataclass
class Chat:
    id: int
    tags: Dict[str, str]
    title: str
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

class BNDAction(Enum):
    delete = 'delete'
    kick = 'kick'
    ban = 'ban'

class CharacterClass(Enum):
    emoji = 'emoji'

@dataclass()
class BND:
    id: int
    chat_id: int
    action: BNDAction
    pattern: Optional[str]
    character_class: CharacterClass
