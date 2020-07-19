import importlib
import os
from dataclasses import dataclass
from importlib._bootstrap import ModuleSpec
from importlib._bootstrap_external import SourceFileLoader
from typing import Callable, List

from telethon import events
from telethon.events.common import EventBuilder

from utils._config import Config


@dataclass
class Command:
    callback: Callable
    private: bool
    command: str


@dataclass
class Event:
    callback: Callable
    event: EventBuilder


class PluginManager:
    commands: List[Command] = []
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

    @classmethod
    def command(cls, command, private=True, *args, **kwargs):
        def decorator(callback):
            plugin = Command(callback, private, command)
            cls.commands.append(plugin)
            return callback

        return decorator

    @classmethod
    def event(cls, event):
        def decorator(callback):
            cls.events.append(Event(callback, event))
            return callback

        return decorator


k = PluginManager
