import inspect
import re
from typing import Callable

from utils._config import Config
from utils.client import KantekClient
from utils.mdtex import *
from utils.pluginmgr import k, _Command, _Event

SECTION_PATTERN = re.compile(r'^(?P<name>[\w ]+:)$', re.MULTILINE)


@k.command('help')
async def help_(client: KantekClient, args, kwargs) -> MDTeXDocument:
    """Get help for kantek commands.

    Examples:
        {cmd} help
        {cmd} autobahn
        {cmd}
    """
    cmds = client.plugin_mgr.commands
    events = client.plugin_mgr.events
    config = Config()
    if not args:
        toc = MDTeXDocument()
        _cmds = []
        for name, cmd in cmds.items():
            _cmds.append(', '.join(cmd.commands))
        _events = []
        toc.append(Section('Command List', *sorted(_cmds)))
        for e in events:
            if e.name:
                _events.append(e.name)
        toc.append(Section('Event List', *sorted(_events)))
        toc.append(Italic('Provide a command/event name as argument to get help for it.'))
        return toc
    if args:
        topic, *subtopic = args
        cmd = cmds.get(topic)
        if cmd is None:
            for _cmd in cmds.values():
                if topic in _cmd.commands:
                    cmd = _cmd
                    break
            for _event in events:
                if _event.name == topic:
                    cmd = _event
                    break
            if cmd is None:
                return MDTeXDocument(Section('Error', f'Unknown command or event {Code(topic)}'))
        if isinstance(cmd, _Command):
            return get_command_info(cmd, subtopic, config)
        elif isinstance(cmd, _Event):
            return get_event_info(cmd, subtopic, config)


def get_event_info(event, subcommands, config) -> MDTeXDocument:
    description = get_description(event.callback, '')
    help_msg = MDTeXDocument(Section(f'Help for {event.name}'), description)
    return help_msg


def get_command_info(cmd, subcommands, config) -> MDTeXDocument:
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
                sc_description = inspect.getdoc(sc.callback)
                if sc_description:
                    sc_description = sc_description.split('\n')[0]
                else:
                    sc_description = Italic('No description provided.')
                subcommands.append(KeyValueItem(Italic(Bold(name)), sc_description,
                                                colon_styles=(Bold, Italic)))
            help_msg.append(subcommands)
        return help_msg
    elif subcommands:
        subcommand = cmd.subcommands.get(subcommands[0])

        if subcommand is None:
            return MDTeXDocument(
                Section('Error', f'Unknown subcommand {Code(subcommands[0])} for command {Code(cmd_name)}'))
        help_cmd = f'{config.help_prefix}{cmd_name} {subcommand.command}'
        description = get_description(subcommand.callback, help_cmd)

        help_msg = MDTeXDocument(Section(f'Help for {help_cmd}'), description)

        return help_msg


def get_description(callback: Callable, help_cmd: str) -> str:
    config = Config()
    description = inspect.getdoc(callback)
    if description is None:
        return 'No description'
    description = description.format(cmd=help_cmd, prefix=config.help_prefix)
    description = SECTION_PATTERN.sub(str(Bold(r'\g<name>')), description)
    return description
