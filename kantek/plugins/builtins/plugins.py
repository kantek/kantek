"""Plugin to get information about a channel."""
from logging import Logger

import logzero
from telethon import events
from telethon.events import NewMessage
from telethon.tl.patched import Message as PMessage

from config import cmd_prefix
from utils.client import KantekClient
from utils.pluginmgr import PluginManager

__version__ = '0.1.0'

logger: Logger = logzero.logger


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}p(lugins)?'))
async def plugins(event: NewMessage.Event) -> None:
    """Show all registered plugins.

    Args:
        event: The event with the command

    Returns: None

    """
    # chat: Channel = event.chat
    client: KantekClient = event.client
    pluginmgr: PluginManager = client.plugin_mgr
    msg: PMessage = event.message
    args = msg.raw_text.split()[1:]
    if not args:
        return
    cmd = args[0]
    if cmd in ['list', 'ls']:
        await _plugins_list(event, client, pluginmgr)


async def _plugins_list(event: NewMessage.Event,
                        client: KantekClient,
                        pluginmgr: PluginManager) -> bool:
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
