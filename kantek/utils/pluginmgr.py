import functools
import importlib
import inspect
import os
from dataclasses import dataclass
from importlib._bootstrap import ModuleSpec
from importlib._bootstrap_external import SourceFileLoader
from typing import Callable, List

from telethon import events
from telethon.events import NewMessage
from telethon.events.common import EventBuilder
from telethon.tl.types import Channel

from utils import helpers
from utils._config import Config
from utils.tagmgr import TagManager


@dataclass
class _Command:
    callback: Callable
    private: bool
    command: str


@dataclass
class Event:
    callback: Callable
    event: EventBuilder


@dataclass
class Signature:
    client: bool = False
    db: bool = False
    chat: bool = False
    msg: bool = False
    args: bool = False
    kwargs: bool = False
    event: bool = False
    tags: bool = False


class PluginManager:
    commands: List[_Command] = []
    events: List[Event] = []

    def __init__(self, client):
        self.client = client
        self.config = Config()
        self._get_plugin_list()

    def _get_plugin_list(self) -> None:
        for root, dirs, files in os.walk(self.config.plugin_path):  # pylint: disable = W0612
            for file in files:
                path = os.path.join(root, file)
                name, ext = os.path.splitext(file)
                if ext == '.py':
                    _module: ModuleSpec = importlib.util.spec_from_file_location(name, path)
                    loader: SourceFileLoader = _module.loader
                    module = loader.load_module()

    def register_all(self):
        for p in self.commands:
            event = events.NewMessage(outgoing=p.private,
                                      pattern=f'{self.config.cmd_prefix}{p.command}')
            self.client.add_event_handler(p.callback, event)

        for e in self.events:
            self.client.add_event_handler(e.callback, e.event)

    @staticmethod
    async def _callback(callback, args: Signature, event):
        callback_args = {}
        client = event.client

        if args.client:
            callback_args['client'] = client

        if args.db:
            callback_args['db'] = client.db

        if args.chat:
            callback_args['chat'] = await event.get_chat()

        if args.msg:
            callback_args['msg'] = event.message

        if args.args or args.kwargs:
            _kwargs, _args = await helpers.get_args(event)
            if args.args:
                callback_args['args'] = _args
            if args.kwargs:
                callback_args['kwargs'] = _kwargs

        if args.event:
            callback_args['event'] = event

        if args.tags:
            callback_args['tags'] = TagManager(event)

        await callback(**callback_args)

    @classmethod
    def command(cls, command, private=True):
        def decorator(callback):
            signature = inspect.signature(callback)
            args = Signature(**{n: True for n in signature.parameters.keys()})
            new_callback = functools.partial(cls._callback, callback, args)
            plugin = _Command(new_callback,
                              private, command)
            cls.commands.append(plugin)

        return decorator

    @classmethod
    def event(cls, event):
        def decorator(callback):
            cls.events.append(Event(callback, event))
            return callback

        return decorator


k = PluginManager

Command = NewMessage.Event
