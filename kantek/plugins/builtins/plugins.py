"""Plugin to interface with the plugin manager."""
from logging import Logger

import logzero
from telethon import events
from telethon.events import NewMessage
from telethon.tl.patched import Message

from config import cmd_prefix
from utils.client import KantekClient
from utils.pluginmgr import PluginManager

__version__ = '0.1.0'

logger: Logger = logzero.logger


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}p(lugins)?'))
async def plugins(event: NewMessage.Event) -> None:
    """Command to show, register and unregister plugins.

    Args:
        event: The event with the command

    Returns: None

    """
    client: KantekClient = event.client
    pluginmgr: PluginManager = client.plugin_mgr
    msg: Message = event.message
    args = msg.raw_text.split()[1:]
    if not args:
        return
    cmd = args[0]
    if cmd in ['list', 'ls']:
        await _plugins_list(event, client, pluginmgr)
    elif cmd in ['unregister', 'ur']:
        await _plugins_unregister(event, client, pluginmgr)
        await _plugins_list(event, client, pluginmgr)


async def _plugins_list(event: NewMessage.Event,
                        client: KantekClient,
                        pluginmgr: PluginManager) -> bool:
    """Get a list of plugins.

    Args:
        event: The event with the command
        client: The client instance
        pluginmgr: The plugin manager instance

    Returns:

    """
    plugin_list = []
    for plugin in pluginmgr.active_plugins:
        plugin_list.append(f'**{plugin.path}:**')
        for callback in plugin.callbacks:
            plugin_list.append(f'  {callback.name}')
    if plugin_list:
        await event.respond('\n'.join(plugin_list),
                            reply_to=(event.reply_to_msg_id or event.message.id))
    else:
        await event.respond('No active plugins.',
                            reply_to=(event.reply_to_msg_id or event.message.id))
    return True


async def _plugins_unregister(event: NewMessage.Event,
                              client: KantekClient,
                              pluginmgr: PluginManager) -> bool:
    """Get a list of plugins.

    Args:
        event: The event with the command
        client: The client instance
        pluginmgr: The plugin manager instance

    Returns:

    """
    args = event.message.raw_text.split()[2:]
    if args[0] == 'all':
        pluginmgr.unregister_all()

    logger.debug(args)
    return True
