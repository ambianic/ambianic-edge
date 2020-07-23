"""Compute differences on a configuration dictionary,
    providing callbacks when a change is detected"""

# This allow python type hints to cross reference objects
# before they are referenced
from __future__ import annotations
from collections.abc import MutableMapping
from typing import Callable, Any, Union
import logging
import copy

log = logging.getLogger(__name__)


class EventContext:
    """Provide contextual information for a reactive configuration object"""

    def __init__(self, name: str, instance: EventHandler = None):
        self.__name = name
        self.__instance = instance

    def get_instance(self) -> EventHandler:
        """Return the object instance"""
        return self.__instance

    def get_name(self) -> str:
        """Return the context name"""
        return self.__name


class ConfigChangedEvent:
    """Information provided when a value change in the configuration"""

    def __init__(
            self,
            name: str,
            op: str,
            context: EventContext,
            value: Any,
            config_tree: list
    ):
        self.__name = name
        self.__op = op
        self.__context = context
        self.value = value
        # dereference list passed as argument
        self.tree = list(config_tree) if config_tree else []
        self.tree.reverse()

    def get_name(self) -> str:
        """return the field contextual name"""
        return self.__name

    def get_operation(self) -> str:
        """return the operation performed on the field"""
        return self.__op

    def get_value(self) -> Any:
        """Return the new value of the field"""
        return self.value

    def get_tree(self) -> list:
        """Return the list of tree elements reaching the root"""
        return self.tree

    def get_paths(self) -> list:
        """Return the tree as a list of field names"""
        paths = []
        for element in self.get_tree():
            if element.get_context():
                paths.append(str(element.get_context().get_name()))
        return paths

    def get_root(self) -> EventHandler:
        """Return the root field element which children changed"""
        tree = self.get_tree()
        if tree is None or len(tree) == 0:
            return None
        return tree[0]

    def get_context(self) -> EventContext:
        """return the event context"""
        return self.__context

    def __repr__(self):
        return str(
            "path=%s name=%s op=%s value=`%s`" % (
                ".".join(self.get_paths()),
                self.get_name(),
                self.get_operation(),
                self.get_value(),
            )
        )


EventCallback = Callable[[ConfigChangedEvent], Any]


class EventHandler:
    """Root class to track callback in an tree-like object structure"""

    def __init__(self):
        self.__context = None
        self.__on_change = []
        self.__initializing = False

    def add_callback(self, on_change: EventCallback):
        """Add a callback called when a value changes"""
        self.__on_change.append(on_change)

    def remove_callback(self, on_change: EventCallback):
        """Remove a callback previously added"""
        if self.__on_change.__contains__(on_change):
            self.__on_change.remove(on_change)
        else:
            log.warning("Can no remove callback: not found")

    def get_context(self) -> EventContext:
        """Return the context class, if any"""
        return self.__context

    def set_context(self, context: EventContext):
        """Set the context class"""
        self.__context = context

    def changed(
            self,
            key: str,
            operation: str,
            new_value: Any,
            config_tree: list = None
    ):
        """trigger a callback when a value has changed"""

        if self.__initializing:
            return

        event_label = ""
        if self.get_context() is not None and self.get_context().get_name():
            event_label += str(self.get_context().get_name())

        if key is not None:
            if event_label != "":
                event_label += "."

            event_label += str(key)

        for callback in self.__on_change:
            changed_event = ConfigChangedEvent(
                key,
                operation,
                self.get_context(),
                new_value,
                config_tree
            )

            # print log only whene at the root items
            # if not self.get_context():
            #     log.debug("Configuration changed: %s", changed_event)

            try:
                callback(changed_event)
            except Exception as exc:
                log.error("Callback error for %s", event_label)
                log.exception(exc, exc_info=True)

        section = self
        if config_tree is None:
            config_tree = [self]
        while section.get_context() and section.get_context().get_instance():
            if not section.get_context().get_instance() in config_tree:
                config_tree.append(section.get_context().get_instance())
                section.get_context().get_instance().changed(
                    key,
                    operation,
                    new_value,
                    config_tree
                )
            section = section.get_context().get_instance()


class ConfigList(EventHandler, list):
    """Extend the base list to trigger when changes happens"""

    def __init__(self, items: list, context: EventContext = None):
        super().__init__()
        self.set_context(context)
        self.__initializing = True
        self.sync(items)
        self.__initializing = False

    def __eq__(self, other):
        if isinstance(other, (ConfigList, list)):
            if len(self) != len(other):
                return False
            for i, val in enumerate(self):
                if val != other[i]:
                    return False
            return True
        return False

    def __wrap_item(self, item: Any, i: int = None):

        if is_value_type(item):
            return item

        type_of = type(item)
        if type_of == list:
            cfglist = ConfigList(item, EventContext(str(i), self))
            return cfglist

        if type_of == ConfigDict:
            return item

        return ConfigDict(item, context=EventContext(str(i), self))

    def sync(self, items):
        """sync a list and attempt to detect changes"""

        if len(self) > 0 and len(items) < len(self):
            self.clear()
            self.changed(None, "remove", None)

        for i, item in enumerate(items):

            element = self.__wrap_item(item, i)

            # is new item?
            if i >= len(self):
                self.append(element)
                continue

            if is_value_type(self[i]):
                self[i] = element
                continue

            self[i].sync(element)

    def remove(self, v):
        item = self.__wrap_item(v)
        res = super().remove(item)
        self.changed(None, "remove", None)
        return res

    def insert(self, i, v):
        item = self.__wrap_item(v)
        res = super().insert(i, item)
        self.changed(None, "add", item)
        return res

    def append(self, v):
        item = self.__wrap_item(v)
        res = super().append(item)
        self.changed(None, "add", item)
        return res

    def extend(self, t):
        res = super().extend([self.__wrap_item(v) for v in t])
        self.changed(None, "set", None)
        return res

    def __add__(self, t):
        res = super().__add__([self.__wrap_item(v) for v in t])
        self.changed(None, "add", None)
        return res

    def __iadd__(self, t):
        res = super().__iadd__([self.__wrap_item(v) for v in t])
        self.changed(None, "add", None)
        return res

    def __setitem__(self, index, value):
        has_changed = str(self[index]) != str(value)
        res = super().__setitem__(index, value)
        if has_changed:
            self.changed(str(index), "set", value)
        return res

    def __delitem__(self, i):
        res = super().__delitem__(i)
        self.changed(str(i), "remove", None)
        return res

    def to_values(self):
        """Return the inner list data as copy"""
        values = []
        for key, val in enumerate(self):
            val = self[key]
            if isinstance(val, (ConfigDict, ConfigList)):
                values[key] = val.to_values()
            elif isinstance(val, (list, dict)):
                values[key] = copy.deepcopy(val)
            else:
                values[key] = val
        return values


class ConfigDict(MutableMapping, EventHandler):
    """Abstract a section of the configuration file"""

    def __init__(self, config: dict, context: EventContext = None):
        super().__init__()
        self.set_context(context)
        self.__data = {}
        self.__initializing = True
        self.sync(config)
        self.__initializing = False

    def sync(self, src_config: Any):
        """Update a configuration tree detecting changes"""
        if src_config is None:
            return

        for key, value in src_config.items():

            # handle simple types
            if is_value_type(value):
                self.set(key, value)
                continue

            # handle list
            if isinstance(value, list):
                cfglist = self.get(key, None)
                if cfglist is None:
                    self.set(key, ConfigList(value, EventContext(key, self)))
                else:
                    cfglist.sync(value)
                continue

            # handle dict
            prev_val = self.get(key, None)
            if prev_val is None:
                self.set(key, ConfigDict(value, context=EventContext(key, self)))
            else:
                prev_val.sync(value)

    def __eq__(self, other):
        return str(self) == str(other)

    def __repr__(self):
        return str(self.__data)

    def __str__(self):
        return str(self.__data)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        del self.__data[key]
        self.changed(key, "remove", None)

    def __iter__(self):
        return iter(self.__data)

    def __len__(self):
        return len(self.__data)

    def __set__(self, obj: Any, value: Any):
        self.set(obj, value)

    def __get__(self, obj: Any, objtype: Any):
        return self.get(obj)

    def get(self, key: str, default_value: Any = None) -> Any:
        """Get a value or a default if not available"""
        return self.__data.get(key, default_value)

    def set(self, key: str, value: Any = None):
        """Set a value"""

        has_changed = False
        if key in self.__data.keys():
            if str(self.__data[key]) != str(value):
                has_changed = True
        else:
            # new key
            self.changed(key, "add", value)

        value = Config(value, context=EventContext(key, self)) if not is_value_type(value) else value

        self.__data[key] = value

        if has_changed:
            self.changed(key, "set", value)

    def to_values(self):
        """Return the inner dict data as copy"""
        values = {}
        for key in self.__data:
            val = self.__data[key]
            if isinstance(val, (ConfigDict, ConfigList)):
                values[key] = val.to_values()
            elif isinstance(val, (list, dict)):
                values[key] = copy.deepcopy(val)
            else:
                values[key] = val
        return values


def Config(values: Any, context: EventContext = None) -> Union[ConfigDict, ConfigList]:
    if isinstance(values, (ConfigList, list)):
        return ConfigList(values, context)
    return ConfigDict(values, context)


def is_value_type(value: Any) -> bool:
    """Check if the argument is a configuration primitive value"""
    return type(value) in (int, float, bool, str)
