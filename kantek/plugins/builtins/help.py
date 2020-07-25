import inspect
import re
from typing import Callable

from utils._config import Config
from utils.client import KantekClient
from utils.mdtex import *
from utils.pluginmgr import k

SECTION_PATTERN = re.compile(r'^(?P<name>[\w ]+:)$', re.MULTILINE)


@k.command('help')
async def help_(client: KantekClient, args, kwargs) -> MDTeXDocument:
    """Get help for kantek commands.

    This currently just outputs the commands docstring.
    It will get more features once the PluginManager gets some upgrades
    """
    cmds = client.plugin_mgr.commands
    config = Config()
    if not args:
        _cmds = []
        for cmd in cmds.values():
            # Replace potential regex characters, commands should probably just
            # be plaint  text and aliases should be handled by the plugin manager though
            _cmds.append(', '.join(cmd.commands))
        return MDTeXDocument(Section('Command List', *sorted(_cmds)),
                             Italic('Provide a command name as argument to get help for it.'))
    if args:
        command, *subcommands = args
        cmd = cmds.get(command)
        if cmd is None:
            for _cmd in cmds.values():
                if command in _cmd.commands:
                    cmd = _cmd
                    break
            if cmd is None:
                return MDTeXDocument(Section('Error', f'Unknown command {Code(command)}'))
        cmd_name = cmd.commands[0]
        if not subcommands:
            help_cmd = f'{config.help_prefix}{cmd_name}'
            description = get_description(cmd.callback, help_cmd)
            help_msg = MDTeXDocument(Section(f'Help for {help_cmd}'), description)

            if cmd.admins:
                help_msg.append(Italic('This command can be used by group admins.'))

            if not cmd.private:
                help_msg.append(Italic('This command is public.'))

            if cmd.subcommands:
                subcommands = Section('Subcommands')
                for name, sc in cmd.subcommands.items():
                    sc_description = inspect.getdoc(sc.callback).split('\n')[0]
                    subcommands.append(KeyValueItem(Italic(Bold(name)), sc_description,
                                                    colon_styles=(Bold, Italic)))
                help_msg.append(subcommands)
            return help_msg
        elif subcommands:
            subcommand = cmd.subcommands.get(subcommands[0])

            if subcommand is None:
                return MDTeXDocument(Section('Error',
                                             f'Unknown subcommand {Code(subcommands[0])} for command {Code(cmd_name)}'))
            help_cmd = f'{config.help_prefix}{cmd_name} {subcommand.command}'
            description = get_description(subcommand.callback, help_cmd)

            help_msg = MDTeXDocument(Section(f'Help for {help_cmd}'), description)

            return help_msg


def get_description(callback: Callable, help_cmd: str) -> str:
    description = inspect.getdoc(callback).format(cmd=help_cmd)
    description = SECTION_PATTERN.sub(str(Bold(r'\g<name>')), description)
    return description
