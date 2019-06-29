import json
import os
from datetime import datetime
from typing import Union

FILE_EXTENSION = '.spjson'


class Strafregister:
    _types = ("ban", "unban")
    BAN, UNBAN = _types

    def __init__(self, file):
        if not file.endswith(FILE_EXTENSION):
            file += FILE_EXTENSION
        self.file = file

    async def log(self, action: str, uid: Union[int, str], reason: str = ''):
        if not self.file:
            return
        current_date = (datetime.utcnow()
                        .replace(microsecond=0)
                        .isoformat())
        header = {"updated": current_date}
        if action in self._types:
            old_list = []
            if os.path.isfile(self.file):
                with open(self.file, 'r') as f:
                    old_list = f.readlines()[1:]

            data = {
                'type': action,
                'id': uid,
                'date': current_date
            }

            if reason:
                data.update({'reason': reason})

            with open(self.file, 'w') as f:
                f.write(json.dumps(header) + '\n')
                new_list = [json.dumps(data) + '\n'] + old_list
                f.write(''.join(new_list))
