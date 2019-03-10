from datetime import datetime
from logging import Handler, LogRecord, Logger
from typing import Union, Dict

import logzero

from vendor import lazybot

logger: Logger = logzero.logger


class TGChannelLogHandler(Handler):
    """Log to a Telegram Channel using a Bot"""

    def __init__(self, bot_token: str, channel_id: Union[str, int]) -> None:
        self.bot = lazybot.Bot(bot_token)
        self.me: Dict[str, Union[bool, str, int]] = self.bot.get_me()
        if not self.me['ok']:
            logger.warning(f'Got Error: {self.me.get("error_code")} {self.me.get("description")} '
                           f'from the bot API. '
                           f'Check if your `log_bot_token` in the config is correct.')

        self.channel_id = channel_id
        super(TGChannelLogHandler, self).__init__()

    def format(self, record: LogRecord) -> str:
        """Format the specified record."""
        time_format = '%Y-%m-%d %H:%M:%S'
        log_time = datetime.fromtimestamp(record.created).strftime(time_format)
        origin = f'`{record.filename}[{record.lineno}]`'
        # only add the function name if the logging call came from one.
        if record.funcName != '<module>':
            origin += f' `❯` `{record.funcName}`'
        _log_entry = {
            'origin': origin,
            'level': f'`{record.levelname.title()}({record.levelno})`',
            'time': f'`{log_time}`',
            'msg': record.getMessage()
        }
        log_entry = []
        for k, v in _log_entry.items():
            log_entry.append(f'`{k}:` {v}')
        return '\n'.join(log_entry)

    def emit(self, record: LogRecord) -> None:
        """Send the log message to the specified Telegram channel."""
        self.bot.send_message(
            chat_id=self.channel_id,
            text=self.format(record),
            parse_mode='markdown')
