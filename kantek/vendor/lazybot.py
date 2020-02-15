"""Super simple bot class to simply call api methods."""
from aiohttp import ClientSession


class Bot:
    """Class containing the needed functions."""

    def __init__(self, token):
        self.url = f'https://api.telegram.org/bot{token}'
        self.aioclient = ClientSession()

    def __getattr__(self, method_name):
        """Allow any method to be called."""

        async def request(**kwargs):
            """Do the post request to telegram."""
            method = self.snake_to_camel(method_name)
            req = await self.aioclient.post(self.url + f'/{method}', data=kwargs)
            result = await req.json()
            return result

        return request

    @staticmethod
    def snake_to_camel(text: str) -> str:
        """Convert snake_case to camelCase."""
        _text = []
        last_char_was_underscore = False
        c: str
        for c in text:
            if c == '_':
                last_char_was_underscore = True
            else:
                if last_char_was_underscore:
                    _text.append(c.upper())
                    last_char_was_underscore = False
                else:
                    _text.append(c)
        return ''.join(_text)
