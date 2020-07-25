import functools
import importlib
import inspect
import os
from dataclasses import dataclass
from importlib._bootstrap import ModuleSpec
from importlib._bootstrap_external import SourceFileLoader
from typing import Callable, List, Dict, Optional

from telethon import events
from telethon.events import NewMessage
from telethon.events.common import EventBuilder
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin

from utils import helpers
from utils._config import Config
from utils.mdtex import MDTeXDocument
from utils.tagmgr import TagManager


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
    args: _Signature
    auto_respond: bool


@dataclass
class _Command:
    callback: Callable
    private: bool
    admins: bool
    command: str
    args: _Signature
    auto_respond: bool

    subcommands: Optional[Dict[str, _SubCommand]] = None

    def subcommand(self, command: str):
        if self.subcommands is None:
            self.subcommands = {}

        def decorator(callback):
            signature = inspect.signature(callback)
            auto_respond = isinstance(signature.return_annotation, MDTeXDocument)
            args = _Signature(**{n: True for n in signature.parameters.keys()})
            cmd = _SubCommand(callback, command, args, auto_respond)
            self.subcommands[command] = cmd
            return cmd

        return decorator


@dataclass
class _Event:
    callback: Callable
    event: EventBuilder


class PluginManager:
    """Load plugins add them as event handlers to the client"""
    commands: Dict[str, _Command] = {}
    events: List[_Event] = []

    def __init__(self, client):
        self.client = client
        self.config = Config()
        self._import_plugins()

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

    def register_all(self):
        """Add all commands and events to the client"""
        for p in self.commands.values():
            pattern = f'{self.config.cmd_prefix}{p.command}'
            if p.admins:
                event = events.NewMessage(pattern=pattern)
            else:
                event = events.NewMessage(outgoing=p.private, pattern=pattern)
            new_callback = functools.partial(self._callback, p, p.args, p.admins)
            self.client.add_event_handler(new_callback, event)

        for e in self.events:
            self.client.add_event_handler(e.callback, e.event)

    @staticmethod
    async def _callback(cmd: _Command, args: _Signature, admins: bool, event) -> None:
        """Wrapper around a plugins callback to dynamically pass requested arguments

        Args:
            args: The arguments of the plugin callback
            event: The NewMessage Event
        """
        client = event.client
        callback = cmd.callback
        skip_args = 1
        if cmd.subcommands:
            msg = event.message
            raw_args = msg.raw_text.split()[1:]
            if raw_args:
                subcommand: Optional[_SubCommand] = cmd.subcommands.get(raw_args[0])
                if subcommand:
                    callback = subcommand.callback
                    skip_args = 2
                    args: _Signature = subcommand.args

        if admins and event.is_channel:
            uid = event.message.from_id
            own_id = (await client.get_me()).id
            result = await client(GetParticipantRequest(event.chat_id, uid))
            if not isinstance(result.participant, ChannelParticipantAdmin) and uid != own_id:
                return

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
            _kwargs, _args = await helpers.get_args(event, skip=skip_args)
            if args.args:
                callback_args['args'] = _args
            if args.kwargs:
                callback_args['kwargs'] = _kwargs

        if args.event:
            callback_args['event'] = event

        if args.tags:
            callback_args['tags'] = TagManager(event)

        result = await callback(**callback_args)
        if cmd.auto_respond:
            await client.respond(event, str(result))

    @classmethod
    def command(cls, command: str, private: bool = True, admins: bool = False):
        """Add a command to the client

        Args:
            command: Regex pattern without command prefix
            private: True if the command should only be run when sent from the user
            admins: Set to True if chat admins should be allowed to use the command too

        Returns:

        """

        def decorator(callback):
            signature = inspect.signature(callback)
            auto_respond = signature.return_annotation is MDTeXDocument
            args = _Signature(**{n: True for n in signature.parameters.keys()})
            cmd = _Command(callback, private, admins, command, args, auto_respond)
            cls.commands[command] = cmd
            return cmd

        return decorator

    @classmethod
    def event(cls, event):
        """Add a Event to the client"""

        def decorator(callback):
            cls.events.append(_Event(callback, event))
            return callback

        return decorator


k = PluginManager

Command = NewMessage.Event
