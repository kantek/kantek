"""File containing the settings for kantek."""
import os
from typing import Union

api_id: Union[str, int] = ''
api_hash: str = ''
phone: str = ''
session_name: str = f'sessions/{os.environ.get("KANTEK_SESSION", "kantek-session")}'

log_bot_token: str = ''
log_channel_id: Union[str, int] = ''

cmd_prefix: str = '.'
