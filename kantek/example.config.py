"""File containing the settings for kantek."""
import os
from typing import Union, List

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

# Optional
# if these options are empty the feature will be disabled.

# The file were bans and unbans are stored
# The extension is .spjson and will be automatically added.
strafregister_file: str = ''

# Channels to fetch bans from
vollzugsanstalten: List[int] = []

spamwatch_host: str = 'https://api.spamwat.ch'
spamwatch_token: str = ''
