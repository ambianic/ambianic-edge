"""Compute differences on a configuration dictionary,
    providing callbacks when a change is detected"""

# This allow python type hints to cross reference objects
# before they are referenced
from __future__ import annotations
from collections.abc import MutableMapping
from typing import Callable, Any
import logging

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
            context: EventContext,
            old_value: Any,
            new_value: Any
    ):
        self.__name = name
        self.__context = context
        self.old_value = old_value
        self.new_value = new_value

    def get_name(self) -> str:
        """return the field contextual name"""
        return self.__name

    def get_context(self) -> EventContext:
        """return the event context"""
        return self.__context

    def __repr__(self):
        return str(
            "%s: new=%s <> old=%s" % (
                self.get_name(),
                self.old_value,
                self.new_value
            )
        )


EventCallback = Callable[[ConfigChangedEvent], Any]


class EventHandler:
    """Root class to track callback in an tree-like object structure"""

    def __init__(self):
        self.__context = None
        self.__on_change = None
        self.__initializing = False

    def set_callback(self, on_change: EventCallback):
        """Set a callback to be called when a value changes"""
        self.__on_change = on_change

    def get_context(self) -> EventContext:
        """Return the context class, if any"""
        return self.__context

    def set_context(self, context: EventContext):
        """Set the context class"""
        self.__context = context

    def changed(self, key: str, old_value: Any, new_value: Any):
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

        log.debug("Configuration property changed: %s", event_label)

        if self.__on_change:
            changed_event = ConfigChangedEvent(
                event_label,
                self.get_context(),
                old_value,
                new_value
            )
            self.__on_change(changed_event)

        if (
                self.get_context() is not None
                and self.get_context().get_instance() is not None
        ):
            self.get_context().get_instance().changed(
                event_label,
                old_value,
                new_value
            )


class Prop(MutableMapping, EventHandler):
    """Watch for property changes and notify by triggering a callback"""

    def __init__(self):
        super().__init__()
        self.__data = {}

    def __eq__(self, other):
        if isinstance(other, Config):
            return str(self) == str(other)
        return False

    def __repr__(self):
        return str(self.__data)

    def __str__(self):
        return str(self.__data)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        self.changed(key, self.__data[key], None)
        del self.__data[key]

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

        old_value = self.__data[key] if key in self.__data.keys() else None

        if key in self.__data.keys():
            if str(self.__data[key]) != str(value):
                old_value = self.__data[key]
                new_value = value
                self.changed(key, old_value, new_value)

        self.__data[key] = value


class ConfigList(EventHandler, list):
    """Extend the base list to trigger when changes happens"""

    def __init__(self, items: list, context: EventContext):
        super().__init__()
        self.set_context(context)
        self.__initializing = True
        self.sync(items)
        self.__initializing = False

    def __eq__(self, other):
        if isinstance(other, ConfigList):
            if len(self) != len(other):
                return False
            for i, val in enumerate(self):
                if val != other[i]:
                    return False
        return True

    def __wrap_item(self, item: Any, i: int = None):

        if is_value_type(item):
            return item

        type_of = type(item)
        if type_of == list:
            cfglist = ConfigList(item, EventContext(i, self))
            return cfglist

        if type_of == Config:
            return item

        return Config(item, EventContext(i, self))

    def sync(self, items):
        """sync a list and attempt to detect changes"""

        if len(self) > 0 and len(items) < len(self):
            self.clear()
            self.changed(None, None, None)

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
        self.changed(None, None, None)
        return res

    def insert(self, i, v):
        item = self.__wrap_item(v)
        res = super().insert(i, item)
        self.changed(None, None, item)
        return res

    def append(self, v):
        item = self.__wrap_item(v)
        res = super().append(item)
        self.changed(None, None, item)
        return res

    def extend(self, t):
        res = super().extend([self.__wrap_item(v) for v in t])
        self.changed(None, None, None)
        return res

    def __add__(self, t):
        res = super().__add__([self.__wrap_item(v) for v in t])
        self.changed(None, None, None)
        return res

    def __iadd__(self, t):
        res = super().__iadd__([self.__wrap_item(v) for v in t])
        self.changed(None, None, None)
        return res

    def __setitem__(self, index, value):
        old_value = self[index]
        new_value = value

        if str(old_value) != str(new_value):
            self.changed(index, old_value, new_value)

        return super().__setitem__(index, value)

    def __delitem__(self, i):
        old_value = self[i]
        new_value = None
        self.changed(i, old_value, new_value)
        return super().__delitem__(i)


class Config(Prop):
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
                self.set(key, Config(value, context=EventContext(key, self)))
            else:
                prev_val.sync(value)


def is_value_type(value: Any) -> bool:
    """Check if the argument is a configuration primitive value"""
    return type(value) in (int, float, bool, str)
