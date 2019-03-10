"""Contains the Plugin Manager handling loading and unloading of plugins."""
import ast
import importlib.util
import os
from importlib._bootstrap import ModuleSpec
from importlib._bootstrap_external import SourceFileLoader
from logging import Logger
from typing import Callable, List, Tuple

import logzero
from telethon import TelegramClient

logger: Logger = logzero.logger


class PluginManager:
    """Mange loading and unloading of plugins."""
    active_plugins: List[Tuple[str, List[str], str]] = []

    def __init__(self, client: TelegramClient) -> None:
        self.client = client
        self.plugin_path: str = os.path.abspath('./plugins')

    def register_all(self) -> List[Tuple[str, List[str], str]]:
        """Get a list of all plugins and register them with the client.

        Returns: List of active plugins

        """
        for plugin_name, path in self._get_plugin_list():
            active_commands = []
            for name, callback in self._get_plugin_callbacks(plugin_name, path):
                logger.debug('Registered plugin %s/%s',
                             self._get_plugin_location(path), name)
                active_commands.append(name)
                self.client.add_event_handler(callback)
            self.active_plugins.append((plugin_name, active_commands, path))
        return self.active_plugins

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

    def _get_plugin_callbacks(self, name: str, path: str) -> List[Tuple[str, Callable]]:
        _module: ModuleSpec = importlib.util.spec_from_file_location(name, path)
        loader: SourceFileLoader = _module.loader
        module = loader.load_module()
        callbacks = []
        with open(path) as f:
            tree = ast.parse(f.read(), filename=path)
            for func in tree.body:
                if isinstance(func, ast.AsyncFunctionDef) and not func.name.startswith('_'):
                    callbacks.append((func.name, getattr(module, func.name)))
        return callbacks
