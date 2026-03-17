"""
Plugin Loader - Discovery and Loading System

BUSINESS CONTEXT:
Discovers, loads, and manages Python plugins that extend the platform.
Similar to Emacs package system for managing extensions.

PLUGIN STRUCTURE:
    plugins/
    └── my-plugin/
        ├── __init__.py       # Plugin entry point
        ├── plugin.yaml       # Plugin metadata
        └── handlers.py       # Plugin code

PLUGIN METADATA (plugin.yaml):
    name: my-plugin
    version: 1.0.0
    description: My awesome plugin
    author: Developer Name
    requires:
      - other-plugin>=1.0
    hooks:
      - before-course-save
      - after-quiz-submit
    events:
      - course.*
      - quiz.submitted

PLUGIN ENTRY POINT (__init__.py):
    from plugin_system import PlatformAPI, hook, EventBus

    def activate(api: PlatformAPI):
        '''Called when plugin is loaded'''
        api.log.info("My plugin activated!")

    def deactivate(api: PlatformAPI):
        '''Called when plugin is unloaded'''
        api.log.info("My plugin deactivated")

    @hook('before-course-save', priority=10)
    def validate_course(course):
        if not course.name:
            raise ValueError("Course must have a name")

@module plugin_loader
"""

import importlib.util
import logging
import os
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

import yaml

logger = logging.getLogger(__name__)


class PluginState(Enum):
    """Plugin lifecycle states."""
    DISCOVERED = "discovered"
    LOADED = "loaded"
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"
    ERROR = "error"


@dataclass
class PluginMetadata:
    """
    Plugin configuration and metadata.

    Loaded from plugin.yaml in the plugin directory.
    """
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    author_email: str = ""
    homepage: str = ""
    license: str = ""
    requires: List[str] = field(default_factory=list)
    hooks: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    settings_schema: Dict[str, Any] = field(default_factory=dict)
    min_platform_version: str = ""
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'PluginMetadata':
        """Load metadata from YAML file."""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f) or {}

        return cls(
            name=data.get('name', yaml_path.parent.name),
            version=data.get('version', '1.0.0'),
            description=data.get('description', ''),
            author=data.get('author', ''),
            author_email=data.get('author_email', ''),
            homepage=data.get('homepage', ''),
            license=data.get('license', ''),
            requires=data.get('requires', []),
            hooks=data.get('hooks', []),
            events=data.get('events', []),
            settings_schema=data.get('settings_schema', {}),
            min_platform_version=data.get('min_platform_version', ''),
            tags=data.get('tags', []),
        )


@dataclass
class Plugin:
    """
    A loaded plugin instance.

    Contains the plugin module, metadata, and runtime state.
    """
    id: str
    metadata: PluginMetadata
    path: Path
    module: Any = None
    state: PluginState = PluginState.DISCOVERED
    error: Optional[str] = None
    loaded_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    settings: Dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def version(self) -> str:
        return self.metadata.version

    def has_function(self, name: str) -> bool:
        """Check if plugin exports a function."""
        return hasattr(self.module, name) and callable(getattr(self.module, name))

    def call_function(self, name: str, *args, **kwargs) -> Any:
        """Call a plugin function if it exists."""
        if self.has_function(name):
            return getattr(self.module, name)(*args, **kwargs)
        return None


class PluginRegistry:
    """
    Central registry of all plugins.

    Tracks plugin state and provides lookup capabilities.
    """

    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._lock = threading.RLock()

    def register(self, plugin: Plugin) -> None:
        """Register a plugin."""
        with self._lock:
            self._plugins[plugin.id] = plugin
            logger.info(f"Registered plugin: {plugin.name} v{plugin.version}")

    def unregister(self, plugin_id: str) -> Optional[Plugin]:
        """Unregister a plugin."""
        with self._lock:
            return self._plugins.pop(plugin_id, None)

    def get(self, plugin_id: str) -> Optional[Plugin]:
        """Get a plugin by ID."""
        with self._lock:
            return self._plugins.get(plugin_id)

    def get_by_name(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        with self._lock:
            for plugin in self._plugins.values():
                if plugin.name == name:
                    return plugin
        return None

    def list_all(self) -> List[Plugin]:
        """List all registered plugins."""
        with self._lock:
            return list(self._plugins.values())

    def list_active(self) -> List[Plugin]:
        """List all activated plugins."""
        with self._lock:
            return [p for p in self._plugins.values() if p.state == PluginState.ACTIVATED]

    def count(self) -> int:
        """Count registered plugins."""
        with self._lock:
            return len(self._plugins)


class PluginLoader:
    """
    Loads and manages plugin lifecycle.

    RESPONSIBILITIES:
    - Discover plugins in configured directories
    - Load and validate plugin code
    - Manage plugin dependencies
    - Handle plugin activation/deactivation
    - Provide hot-reload capabilities

    Example:
        loader = PluginLoader('/path/to/plugins')
        loader.discover_all()
        loader.load_all()
        loader.activate_all()

        # Later, reload a specific plugin
        loader.reload('my-plugin')

        # Unload on shutdown
        loader.deactivate_all()
    """

    def __init__(
        self,
        plugin_dirs: Optional[List[str]] = None,
        registry: Optional[PluginRegistry] = None
    ):
        """
        Initialize the plugin loader.

        Args:
            plugin_dirs: List of directories to search for plugins
            registry: Plugin registry (creates new if not provided)
        """
        self.plugin_dirs = [Path(d) for d in (plugin_dirs or [])]
        self.registry = registry or PluginRegistry()
        self._api = None  # Set by platform during initialization
        self._lock = threading.RLock()

    def set_api(self, api: Any) -> None:
        """Set the PlatformAPI instance for plugins to use."""
        self._api = api

    def add_plugin_dir(self, directory: str) -> None:
        """Add a directory to search for plugins."""
        path = Path(directory)
        if path not in self.plugin_dirs:
            self.plugin_dirs.append(path)

    def discover_all(self) -> List[Plugin]:
        """
        Discover all plugins in configured directories.

        Returns:
            List of discovered plugins
        """
        discovered = []

        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                logger.warning(f"Plugin directory does not exist: {plugin_dir}")
                continue

            # Look for plugin directories (containing __init__.py)
            for item in plugin_dir.iterdir():
                if item.is_dir():
                    init_file = item / '__init__.py'
                    if init_file.exists():
                        plugin = self._discover_plugin(item)
                        if plugin:
                            discovered.append(plugin)

        logger.info(f"Discovered {len(discovered)} plugins")
        return discovered

    def _discover_plugin(self, plugin_path: Path) -> Optional[Plugin]:
        """
        Discover a single plugin.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Plugin instance or None
        """
        try:
            # Load metadata
            metadata_file = plugin_path / 'plugin.yaml'
            if metadata_file.exists():
                metadata = PluginMetadata.from_yaml(metadata_file)
            else:
                # Use directory name as plugin name
                metadata = PluginMetadata(name=plugin_path.name)

            plugin_id = f"{metadata.name}@{metadata.version}"
            plugin = Plugin(
                id=plugin_id,
                metadata=metadata,
                path=plugin_path,
                state=PluginState.DISCOVERED
            )

            self.registry.register(plugin)
            return plugin

        except Exception as e:
            logger.error(f"Failed to discover plugin at {plugin_path}: {e}")
            return None

    def load(self, plugin_id: str) -> bool:
        """
        Load a plugin module.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if loaded successfully
        """
        plugin = self.registry.get(plugin_id)
        if not plugin:
            logger.error(f"Plugin not found: {plugin_id}")
            return False

        if plugin.state == PluginState.LOADED:
            logger.debug(f"Plugin already loaded: {plugin_id}")
            return True

        try:
            # Check dependencies
            for dep in plugin.metadata.requires:
                if not self._check_dependency(dep):
                    raise ImportError(f"Missing dependency: {dep}")

            # Load the module
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin.name}",
                plugin.path / '__init__.py'
            )

            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)

                plugin.module = module
                plugin.state = PluginState.LOADED
                plugin.loaded_at = datetime.now()
                plugin.error = None

                logger.info(f"Loaded plugin: {plugin.name} v{plugin.version}")
                return True
            else:
                raise ImportError(f"Could not load spec for {plugin.path}")

        except Exception as e:
            plugin.state = PluginState.ERROR
            plugin.error = str(e)
            logger.error(f"Failed to load plugin {plugin_id}: {e}")
            return False

    def _check_dependency(self, dependency: str) -> bool:
        """Check if a dependency is satisfied."""
        # Parse dependency string (e.g., "other-plugin>=1.0")
        parts = dependency.split('>=')
        dep_name = parts[0].strip()

        # Check if dependency is registered and activated
        dep_plugin = self.registry.get_by_name(dep_name)
        if not dep_plugin:
            return False

        if len(parts) > 1:
            # Version check (simplified)
            required_version = parts[1].strip()
            if dep_plugin.version < required_version:
                return False

        return dep_plugin.state in [PluginState.LOADED, PluginState.ACTIVATED]

    def activate(self, plugin_id: str) -> bool:
        """
        Activate a loaded plugin.

        Calls the plugin's activate() function if defined.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if activated successfully
        """
        plugin = self.registry.get(plugin_id)
        if not plugin:
            logger.error(f"Plugin not found: {plugin_id}")
            return False

        if plugin.state != PluginState.LOADED:
            if plugin.state == PluginState.ACTIVATED:
                return True
            logger.error(f"Plugin not loaded: {plugin_id}")
            return False

        try:
            # Call activate function if defined
            if plugin.has_function('activate'):
                plugin.call_function('activate', self._api)

            plugin.state = PluginState.ACTIVATED
            plugin.activated_at = datetime.now()
            plugin.error = None

            logger.info(f"Activated plugin: {plugin.name}")
            return True

        except Exception as e:
            plugin.state = PluginState.ERROR
            plugin.error = str(e)
            logger.error(f"Failed to activate plugin {plugin_id}: {e}")
            return False

    def deactivate(self, plugin_id: str) -> bool:
        """
        Deactivate an active plugin.

        Calls the plugin's deactivate() function if defined.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if deactivated successfully
        """
        plugin = self.registry.get(plugin_id)
        if not plugin:
            logger.error(f"Plugin not found: {plugin_id}")
            return False

        if plugin.state != PluginState.ACTIVATED:
            return True

        try:
            # Call deactivate function if defined
            if plugin.has_function('deactivate'):
                plugin.call_function('deactivate', self._api)

            # Clean up hooks and event subscriptions
            from plugin_system.core.hook_manager import HookManager
            from plugin_system.core.event_bus import EventBus

            HookManager.get_instance().remove_plugin(plugin_id)
            EventBus.get_instance().unsubscribe_plugin(plugin_id)

            plugin.state = PluginState.DEACTIVATED
            logger.info(f"Deactivated plugin: {plugin.name}")
            return True

        except Exception as e:
            logger.error(f"Error deactivating plugin {plugin_id}: {e}")
            return False

    def reload(self, plugin_id: str) -> bool:
        """
        Reload a plugin (deactivate, unload, load, activate).

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if reloaded successfully
        """
        plugin = self.registry.get(plugin_id)
        if not plugin:
            return False

        self.deactivate(plugin_id)

        # Remove from sys.modules to force reload
        module_name = f"plugins.{plugin.name}"
        if module_name in sys.modules:
            del sys.modules[module_name]

        plugin.state = PluginState.DISCOVERED
        plugin.module = None

        return self.load(plugin_id) and self.activate(plugin_id)

    def load_all(self) -> Dict[str, bool]:
        """
        Load all discovered plugins.

        Returns:
            Dict of plugin_id -> success
        """
        results = {}
        for plugin in self.registry.list_all():
            if plugin.state == PluginState.DISCOVERED:
                results[plugin.id] = self.load(plugin.id)
        return results

    def activate_all(self) -> Dict[str, bool]:
        """
        Activate all loaded plugins.

        Returns:
            Dict of plugin_id -> success
        """
        results = {}
        for plugin in self.registry.list_all():
            if plugin.state == PluginState.LOADED:
                results[plugin.id] = self.activate(plugin.id)
        return results

    def deactivate_all(self) -> Dict[str, bool]:
        """
        Deactivate all active plugins.

        Returns:
            Dict of plugin_id -> success
        """
        results = {}
        for plugin in self.registry.list_active():
            results[plugin.id] = self.deactivate(plugin.id)
        return results

    def get_plugin_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all plugins.

        Returns:
            List of plugin status dicts
        """
        return [
            {
                'id': p.id,
                'name': p.name,
                'version': p.version,
                'state': p.state.value,
                'error': p.error,
                'loaded_at': p.loaded_at.isoformat() if p.loaded_at else None,
                'activated_at': p.activated_at.isoformat() if p.activated_at else None,
                'description': p.metadata.description,
                'author': p.metadata.author,
            }
            for p in self.registry.list_all()
        ]
