"""File containing the settings for kantek."""
import os

api_id = ''
api_hash = ''
phone = ''
session_name = f'sessions/{os.environ.get("KANTEK_SESSION", "kantek-session")}'

log_bot_token = ''
log_channel_id = ''
