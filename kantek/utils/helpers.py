from telethon.tl.types import User


async def get_full_name(user: User):
    """Return first_name + last_name if last_name exists else just first_name

    Args:
        user: The user

    Returns:
        The combined names
    """
    return user.first_name + ' ' + (user.last_name or '')
