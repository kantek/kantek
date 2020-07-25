import inspect

from utils.client import KantekClient
from utils.pluginmgr import k
from utils.mdtex import *


@k.command('help')
async def help_(client: KantekClient, args, kwargs) -> MDTeXDocument:
    """Get help for kantek commands.

    This currently just outputs the commands docstring.
    It will get more features once the PluginManager gets some upgrades
    """
    cmds = client.plugin_mgr.commands
    if not args:
        _cmds = []
        for cmd in cmds.keys():
            # Replace potential regex characters, commands should probably just
            # be plaint  text and aliases should be handled by the plugin manager though
            _cmds.append(cmd.replace('(', '').replace(')', '').replace('?', ''))
        return MDTeXDocument(Section('Command List', *sorted(_cmds)),
                             Italic('Provide a command name as argument to get help for it.'))
    if args:
        cmd = cmds.get(args[0])
        if cmd is None:
            return MDTeXDocument(Section('Error', f'Unknown command `{args[0]}`'))

        else:
            cmd_name = cmd.command.replace('(', '').replace(')', '').replace('?', '')
            return MDTeXDocument(Section(f'Help for {cmd_name}'), inspect.getdoc(cmd.callback))
