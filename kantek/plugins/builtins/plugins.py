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


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}plugins'))
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
    response = False
    if not args:
        response = await _plugins_list(pluginmgr)
    else:
        cmd = args[0]
        if cmd in ['list', 'ls']:
            response = await _plugins_list(pluginmgr)
        elif cmd in ['unregister', 'ur']:
            response = await _plugins_unregister(event, pluginmgr)
    await client.respond(event, response)


async def _plugins_list(pluginmgr: PluginManager) -> str:
    """Get a list of plugins.

    Args:
        pluginmgr: The plugin manager instance

    Returns:

    """
    plugin_list = []
    for plugin in pluginmgr.active_plugins:
        plugin_list.append(f'**{plugin.path} [{plugin.version}]:**')
        for callback in plugin.callbacks:
            prefix = "[private]" if callback.private else "[public]"
            plugin_list.append(f'  {prefix} {callback.name}')
    if plugin_list:
        return '\n'.join(plugin_list)
    else:
        return 'No active plugins.'


async def _plugins_unregister(event: NewMessage.Event,
                              pluginmgr: PluginManager) -> str:
    """Get a list of plugins.

    Args:
        event: The event with the command
        pluginmgr: The plugin manager instance

    Returns:

    """
    args = event.message.raw_text.split()[2:]
    if not args:
        return 'No arguments specified.'
    if args[0] == 'all':
        pluginmgr.unregister_all()

    return 'Unregistered all non builtins.'
