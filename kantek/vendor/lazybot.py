"""Super simple bot class to simply call api methods."""
import requests


class Bot:
    """Class containing the needed functions."""
    def __init__(self, token):
        self.url = f'https://api.telegram.org/bot{token}'

    def __getattr__(self, method_name):
        """Allow any method to be called."""
        def request(**kwargs):
            """Do the post request to telegram."""
            method = self.snake_to_camel(method_name)
            req = requests.post(self.url + f'/{method}', data=kwargs)
            return req.json()

        return request

    def snake_to_camel(self, text: str) -> str:
        """Convert snake_case to camelCase."""
        _text = []
        last_char_was_underscore = False
        c: str
        for i, c in enumerate(text):
            if c == '_':
                last_char_was_underscore = True
            else:
                if last_char_was_underscore:
                    _text.append(c.upper())
                    last_char_was_underscore = False
                else:
                    _text.append(c)
        return ''.join(_text)
