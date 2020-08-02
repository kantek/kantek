import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import logzero

logger = logzero.setup_logger('kantek-logger', level=logging.DEBUG)
tlog = logging.getLogger('kantek-channel-log')


@dataclass
class ConfigWrapper:
    api_id: int
    api_hash: str
    phone: str

    db_password: str

    log_bot_token: str
    log_channel_id: int

    gban_group: int

    plugin_path: str

    db_type: str = 'postgres'
    db_username: str = "kantek"
    db_name: str = "kantek"
    db_host: str = '127.0.0.1'
    db_port: int = None

    cmd_prefix: List[str] = field(default_factory=lambda: ['.'])

    session_name: str = 'kantek-session'

    spamwatch_host: str = 'https://api.spamwat.ch'
    spamwatch_token: str = None

    debug_mode: bool = False

    source_url: str = 'src.kv2.dev'


class Config:  # pylint: disable = R0902
    """Handle loading config options"""
    instance = None

    def __new__(cls):
        if cls.instance is not None:
            return cls.instance
        bot_dir = Path(__file__).parent.parent
        sessions_dir = bot_dir / 'sessions'
        plugin_path = bot_dir / 'plugins'
        repo_dir = bot_dir.parent
        config_path = repo_dir / 'config.json'
        if config_path.is_file():
            with open(config_path) as f:
                config = json.load(f)
                config['plugin_path'] = plugin_path
                if prefix := config.get('cmd_prefix'):
                    if isinstance(prefix, str):
                        config['cmd_prefix'] = [prefix]
                cfg = ConfigWrapper(**config)
                cfg.session_name = (sessions_dir / cfg.session_name).absolute()
                cls.instance = cfg
                return cfg
