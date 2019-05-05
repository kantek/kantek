"""File containing the settings for kantek."""
import os
from typing import Union

api_id: Union[str, int] = ''
api_hash: str = ''
phone: str = ''
session_name: str = f'sessions/{os.environ.get("KANTEK_SESSION", "kantek-session")}'

log_bot_token: str = ''
log_channel_id: Union[str, int] = ''

gban_group = ''

# This is regex so make sure to escape the usual characters
cmd_prefix: str = r'\.'

db_username = 'kantek'
db_name = 'kantek'
db_password = 'PASSWORD'
db_host = 'http://127.0.0.1:8529'
