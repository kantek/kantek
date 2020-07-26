import inspect
import re
from typing import Callable

from utils._config import Config
from utils.client import Client
from utils.mdtex import *
from utils.pluginmgr import k, _Command, _Event

SECTION_PATTERN = re.compile(r'^(?P<name>[\w ]+:)$', re.MULTILINE)

MISC_TOPICS = ['parsers']


@k.command('help')
async def help_(client: Client, args, kwargs) -> MDTeXDocument:
    """Get help for kantek commands.

    Arguments:
        `topic`: A help topic as listed by {prefix}help
        `subtopic`: Optional subtopic like subcommands

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
        if topic in MISC_TOPICS:
            return get_misc_topics(topic, subtopic)
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


def get_misc_topics(topic, subtopics) -> MDTeXDocument:
    subtopic = None
    if subtopics:
        subtopic = subtopics[0]
    if topic == 'parsers':
        if not subtopic:
            return MDTeXDocument(
                Section(f'Available Parsers',
                        KeyValueItem(Italic(Bold('time')),
                                     'Specify durations with a shorthand',
                                     colon_styles=(Bold, Italic))))
        elif subtopic == 'time':
            return MDTeXDocument(
                Section('Time'),
                'Express a duration as a shorthand:\n'
                'Supports s, m, h, d and w for seconds, minutes, hours, days and weeks respectively.',
                Section('Examples:',
                        KeyValueItem(Code('1s'), '1 second'),
                        KeyValueItem(Code('20m'), '20 minutes'),
                        KeyValueItem(Code('3h'), '3 hours'),
                        KeyValueItem(Code('3h1d'), '3 hours and 1 day (27 hours)'),
                        KeyValueItem(Code('1w2d'), '1 week and 2 days (9 days)'),
                        KeyValueItem(Code('20m30s'), '20 minutes and 30 seconds'))
            )
