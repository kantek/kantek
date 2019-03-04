import logging
from datetime import datetime
from logging import Handler, LogRecord

import config
from vendor import lazybot


class TGChannelLogHandler(Handler):
    """Log to a Telegram Channel using a Bot"""

    def __init__(self, bot_token, channel_id):
        self.bot = lazybot.Bot(bot_token)
        self.channel_id = channel_id
        super(TGChannelLogHandler, self).__init__()

    def format(self, record: LogRecord):
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

    def emit(self, record) -> dict:
        """Log the message"""
        message = self.bot.send_message(
            chat_id=self.channel_id,
            text=self.format(record),
            parse_mode='markdown')
        return message
