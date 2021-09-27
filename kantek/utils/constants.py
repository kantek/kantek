from telethon.errors import (UsernameInvalidError, UsernameNotOccupiedError, InviteHashInvalidError,
                             AuthBytesInvalidError, FileIdInvalidError, PeerIdInvalidError, FileReferenceExpiredError, )

TELEGRAM_DOMAINS = ['t.me',
                    'telegram.org',
                    'telegram.dog',
                    'telegra.ph',
                    'tdesktop.com',
                    'telesco.pe',
                    'graph.org',
                    'contest.dev']

GET_ENTITY_ERRORS = (UsernameNotOccupiedError, UsernameInvalidError, ValueError, InviteHashInvalidError, PeerIdInvalidError)

DOWNLOAD_ERRORS = (AuthBytesInvalidError, FileIdInvalidError, FileReferenceExpiredError)
