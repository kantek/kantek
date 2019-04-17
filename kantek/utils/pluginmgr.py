"""Contains the Plugin Manager handling loading and unloading of plugins."""
import ast
import importlib.util
import os
from dataclasses import dataclass
from importlib._bootstrap import ModuleSpec
from importlib._bootstrap_external import SourceFileLoader
from logging import Logger
from typing import Callable, List, Tuple

import logzero
from telethon import TelegramClient

logger: Logger = logzero.logger

__version__ = '0.1.0'


@dataclass
class Callback:
    name: str
    callback: Callable


@dataclass
class Plugin:
    """A Plugin with callbacks.

    Attributes:
        name: Plugin name without path
        callbacks: List of callbacks the plugin has
        full_path: Absolute path to the plugin
        plugin_path: Plugin folder the plugin lies in
        path: Plugin Path relative to the Plugin Folder
    """
    name: str
    callbacks: List[Callback]
    full_path: str
    plugin_path: str

    @property
    def path(self):
        """Return the plugin path relative to the plugin folder."""
        return (os.path.relpath(self.full_path, self.plugin_path)
                .rstrip('.py')
                # replace the backslash in windows paths
                .replace('\\', '/'))


class PluginManager:
    """Mange loading and unloading of plugins."""
    active_plugins: List[Plugin] = []

    def __init__(self, client: TelegramClient) -> None:
        self.client = client
        self.plugin_path: str = os.path.abspath('./plugins')

    def register_all(self) -> List[Plugin]:
        """Get a list of all plugins and register them with the client.

        Returns: List of active plugins

        """
        for plugin_name, path in self._get_plugin_list():
            active_commands = []
            for callback in self._get_plugin_callbacks(plugin_name, path):
                logger.debug('Registered plugin %s/%s',
                             self._get_plugin_location(path), callback.name)
                active_commands.append(callback)
                self.client.add_event_handler(callback.callback)
            self.active_plugins.append(
                Plugin(plugin_name,
                       active_commands,
                       path,
                       self.plugin_path))

        logger.info(f'Registered {len(self.active_plugins)} plugins.')
        return self.active_plugins

    def unregister_all(self, builtins=False) -> None:
        for plugin in self.active_plugins:
            if builtins:
                self.unregister_plugin(plugin)
            else:
                if not plugin.path.startswith('builtins/'):
                    self.unregister_plugin(plugin)

    def unregister_plugin(self, plugin: Plugin):
        for callback in plugin.callbacks:
            logger.debug(self.client.remove_event_handler(callback.callback))
        self.active_plugins.remove(plugin)

    def _get_plugin_location(self, path: str) -> str:
        return (os.path.relpath(path, self.plugin_path)
                .rstrip('.py')
                # replace the backslash in windows paths
                .replace('\\', '/'))

    def _get_plugin_list(self) -> List[Tuple[str, str]]:
        plugins: List[Tuple[str, str]] = []
        for root, dirs, files in os.walk(self.plugin_path):
            for file in files:
                path = os.path.join(root, file)
                name, ext = os.path.splitext(file)
                if ext == '.py':
                    plugins.append((name, path))
        return plugins

    def _get_plugin_callbacks(self, name: str, path: str) -> List[Callback]:
        _module: ModuleSpec = importlib.util.spec_from_file_location(name, path)
        loader: SourceFileLoader = _module.loader
        module = loader.load_module()
        callbacks = []
        with open(path) as f:
            tree = ast.parse(f.read(), filename=path)
            for func in tree.body:
                if isinstance(func, ast.AsyncFunctionDef) and not func.name.startswith('_'):
                    callbacks.append(Callback(func.name, getattr(module, func.name)))
        return callbacks
