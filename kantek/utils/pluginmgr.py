import functools
import importlib
import inspect
import logging
import os
import re
import traceback
from dataclasses import dataclass
from importlib._bootstrap import ModuleSpec
from importlib._bootstrap_external import SourceFileLoader
from typing import Callable, List, Dict, Optional, Tuple

from telethon import events
from telethon.events import NewMessage
from telethon.events.common import EventBuilder
from telethon.tl.custom import Forward, Message
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin

from utils import helpers
from utils._config import Config
from utils.mdtex import *
from utils.tags import Tags

tlog = logging.getLogger('kantek-channel-log')


@dataclass
class _Signature:  # pylint: disable = R0902
    client: bool = False
    db: bool = False
    chat: bool = False
    msg: bool = False
    args: bool = False
    kwargs: bool = False
    event: bool = False
    tags: bool = False


@dataclass
class _SubCommand:
    callback: Callable
    command: str
    signature: _Signature
    auto_respond: bool


@dataclass
class _Command:
    callback: Callable
    private: bool
    admins: bool
    commands: Tuple[str]
    signature: _Signature
    auto_respond: bool
    document: bool = True

    subcommands: Optional[Dict[str, _SubCommand]] = None

    def subcommand(self, command: Optional[str] = None):
        if self.subcommands is None:
            self.subcommands = {}

        def decorator(callback: Callable):
            _command: Optional[str] = command
            if _command is None:
                _command = callback.__name__.rstrip('_')
            signature = inspect.signature(callback)
            auto_respond = signature.return_annotation is MDTeXDocument
            args = _Signature(**{n: True for n in signature.parameters.keys()})
            cmd = _SubCommand(callback, _command, args, auto_respond)
            self.subcommands[_command] = cmd
            return cmd

        return decorator


@dataclass
class _Event:
    callback: Callable
    event: EventBuilder
    name: Optional[str]


class PluginManager:
    """Load plugins add them as event handlers to the client"""
    commands: Dict[str, _Command] = {}
    events: List[_Event] = []

    def __init__(self, client):
        self.client = client
        self.config = Config()
        self._import_plugins()

    @classmethod
    def command(cls, *commands: str, private: bool = True, admins: bool = False, document: bool = True):
        """Add a command to the client

        Args:
            commands: Command names to be used, will be concated using regex
            private: True if the command should only be run when sent from the user
            admins: Set to True if chat admins should be allowed to use the command too
            document: If the help command should list this command

        Returns:

        """
        if not commands:
            raise SyntaxError('Command must have at least one command name')

        def decorator(callback):
            signature = inspect.signature(callback)
            auto_respond = signature.return_annotation is MDTeXDocument or signature.return_annotation is Optional[
                MDTeXDocument]
            args = _Signature(**{n: True for n in signature.parameters.keys()})
            cmd = _Command(callback, private, admins, commands, args, auto_respond, document)
            cls.commands[commands[0]] = cmd
            return cmd

        return decorator

    @classmethod
    def event(cls, event, name: str = None):
        """Add a Event to the client"""

        def decorator(callback):
            cls.events.append(_Event(callback, event, name))
            return callback

        return decorator

    def register_all(self):
        """Add all commands and events to the client"""
        for p in self.commands.values():
            pattern = re.compile(fr'{self.config.cmd_prefix}({"|".join(p.commands)})\b', re.I)
            if p.admins:
                event = events.NewMessage(pattern=pattern)
            else:
                event = events.NewMessage(outgoing=p.private, pattern=pattern)
            new_callback = functools.partial(self._callback, p, p.signature, p.admins)
            self.client.add_event_handler(new_callback, event)

        for e in self.events:
            self.client.add_event_handler(functools.partial(self._event_callback, e), e.event)

    def _import_plugins(self) -> None:
        """Import all plugins so the decorators are run"""
        for root, dirs, files in os.walk(str(self.config.plugin_path)):  # pylint: disable = W0612
            for file in files:
                path = os.path.join(root, file)
                name, ext = os.path.splitext(file)
                if ext == '.py':
                    _module: ModuleSpec = importlib.util.spec_from_file_location(name, path)
                    loader: SourceFileLoader = _module.loader
                    loader.load_module()

    @staticmethod
    async def _event_callback(event: _Event, tg_event) -> None:
        try:
            await event.callback(tg_event)
        except Exception as err:
            name = event.callback.__name__
            tlog.error(f'An error occured in the event `{name}`', exc_info=err)

    @staticmethod
    async def _callback(cmd: _Command, args: _Signature, admins: bool, event: NewMessage.Event) -> None:
        """Wrapper around a plugins callback to dynamically pass requested arguments

        Args:
            args: The arguments of the plugin callback
            event: The NewMessage Event
        """
        client = event.client
        msg: Message = event.message
        if msg.via_bot_id is not None:
            return
        if msg.forward is not None:
            forward: Forward = msg.forward
            me = await client.get_me()
            if forward.sender_id is None or forward.sender_id != me.id:
                return
        if msg.sticker is not None or msg.dice is not None:
            return
        callback = cmd.callback
        skip_args = 1
        help_topic = [cmd.commands[0]]
        if cmd.subcommands:
            raw_args = msg.raw_text.split()[1:]
            if raw_args:
                subcommand: Optional[_SubCommand] = cmd.subcommands.get(raw_args[0])
                if subcommand:
                    callback = subcommand.callback
                    skip_args = 2
                    args: _Signature = subcommand.signature
                    cmd: _SubCommand = subcommand
                    help_topic.append(cmd.command)

        _kwargs, _args = await helpers.get_args(event, skip=skip_args)

        if admins and event.is_channel:

            uid = event.message.from_id
            own_id = (await client.get_me()).id
            if uid != own_id and _kwargs.get('self', False):
                return
            result = await client(GetParticipantRequest(event.chat_id, uid))
            if not isinstance(result.participant, ChannelParticipantAdmin) and uid != own_id:
                return

        if _kwargs.get('help', False):
            _cmd: Optional[_Command] = PluginManager.commands.get('help')
            if _cmd:
                cmd = _cmd
                args: _Signature = cmd.signature
                callback = cmd.callback
                _args = help_topic
                _kwargs = {}

        callback_args = {}

        if args.client:
            callback_args['client'] = client

        if args.db:
            callback_args['db'] = client.db

        if args.chat:
            callback_args['chat'] = await event.get_chat()

        if args.msg:
            callback_args['msg'] = event.message

        if args.args or args.kwargs:
            if args.args:
                callback_args['args'] = _args
            if args.kwargs:
                callback_args['kwargs'] = _kwargs

        if args.event:
            callback_args['event'] = event

        if args.tags:
            callback_args['tags'] = Tags(event)

        try:
            result = await callback(**callback_args)
            if result and cmd.auto_respond:
                await client.respond(event, str(result))
        except Exception as err:
            command = ''
            if isinstance(cmd, _Command):
                command = cmd.commands[0]
            elif isinstance(cmd, _SubCommand):
                command = cmd.command
            tlog.error(f'An error occured while running `{command}`', exc_info=err)


k = PluginManager

Command = NewMessage.Event
