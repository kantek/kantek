import json
from pathlib import Path
from typing import List, Dict


class Config:
    api_id: int
    api_hash: str
    phone: str

    db_username: str = "kantek"
    db_name: str = "kantek"
    db_password: str
    db_host: str = 'http://127.0.0.1:8529'

    log_bot_token: str
    log_channel_id: int

    gban_group: int

    cmd_prefix: str = r'\.'
    session_name: str = 'kantek-session'

    spamwatch_host: str = 'https://api.spamwat.ch'
    spamwatch_token: str = None

    plugin_path: Path

    def __init__(self):
        try:
            import config
            legacy_config = config
        except ImportError:
            legacy_config = None

        bot_dir = Path(__file__).parent.parent
        sessions_dir = bot_dir / 'sessions'
        self.plugin_path = bot_dir / 'plugins'
        repo_dir = bot_dir.parent
        new_config = repo_dir / 'config.json'

        if new_config.is_file():
            with open(new_config) as f:
                config = json.load(f)
            error = False if legacy_config else True
            self.from_json(config, error)
        # legacy config used a full path instead of just a name
        self.session_name = sessions_dir / self.session_name

        if legacy_config:
            self.from_legacy_module(legacy_config)

    def from_json(self, config: Dict, error):
        # error keyword is temporary until the old config is removed fully
        self.api_id = config.get('api_id')
        if error:
            assert self.api_id is not None, "api_id is not set"
        self.api_hash = config.get('api_hash')
        if error:
            assert self.api_hash is not None, "api_hash is not set"
        self.phone = config.get('phone')
        if error:
            assert self.phone is not None, "phone is not set"

        self.log_bot_token = config.get('log_bot_token')
        if error:
            assert self.log_bot_token is not None, "log_bot_token is not set"
        self.log_channel_id = config.get('log_channel_id')
        if error:
            assert self.log_channel_id is not None, "log_channel_id is not set"
        self.gban_group = config.get('gban_group')
        if error:
            assert self.gban_group is not None, "gban_group is not set"
        self.db_username = config.get('db_username', self.db_username)
        self.db_name = config.get('db_name', self.db_name)
        self.db_password = config.get('db_password')
        if error:
            assert self.db_password is not None, "db_password is not set"
        self.db_host = config.get('db_host', self.db_host)

        self.session_name = config.get('session_name', self.session_name)
        self.cmd_prefix = config.get('cmd_prefix', self.cmd_prefix)
        self.spamwatch_host = config.get('spamwatch_host', self.spamwatch_host)
        self.spamwatch_token = config.get('spamwatch_token', self.spamwatch_token)

    def from_legacy_module(self, module):
        self.api_id = getattr(module, 'api_id')
        self.api_hash = getattr(module, 'api_hash')
        self.phone = getattr(module, 'phone')

        self.db_username = getattr(module, 'db_username', self.db_username)
        self.db_name = getattr(module, 'db_name', self.db_name)
        self.db_password = getattr(module, 'db_password')
        self.db_host = getattr(module, 'db_host', self.db_host)
        self.log_bot_token = getattr(module, 'log_bot_token')
        self.log_channel_id = getattr(module, 'log_channel_id')
        self.gban_group = getattr(module, 'gban_group')

        self.session_name = getattr(module, 'session_name', self.session_name)
        self.cmd_prefix = getattr(module, 'cmd_prefix', self.cmd_prefix)
        self.spamwatch_host = getattr(module, 'spamwatch_host', self.spamwatch_host)
        self.spamwatch_token = getattr(module, 'spamwatch_token', self.spamwatch_token)
