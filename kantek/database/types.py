from dataclasses import dataclass
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


@dataclass
class BannedUser:
    id: int
    reason: str
