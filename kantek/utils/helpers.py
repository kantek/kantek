"""Helper functions to aid with different tasks that dont require a client."""
from telethon.tl.types import User


async def get_full_name(user: User) -> str:
    """Return first_name + last_name if last_name exists else just first_name

    Args:
        user: The user

    Returns:
        The combined names
    """
    return str(user.first_name + ' ' + (user.last_name or ''))
