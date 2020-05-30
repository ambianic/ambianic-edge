from typing import Callable


class ConfigChangedEvent:
    """Information provided when a value change in the configuration"""

    def __init__(self, name: any, object: any):
        self.name = name
        self.object = object

    def __repr__(self):
        return str(self.name)


class Prop:
    """Watch for property changes and notify by triggering a callback"""

    def __init__(self, parent: any):
        self.__data = {}
        self.__parent = parent
        self.on_change = None

    def set_callback(self, on_change: Callable[[ConfigChangedEvent], any]):
        """Set a callback to be called when a value changes"""
        self.on_change = on_change

    def get_parent(self):
        """Return the class parent if any"""
        return self.__parent

    def __changed(self, key: any):
        if self.on_change:
            self.on_change(ConfigChangedEvent(key, self))

        while self.get_parent() is not None:
            if self.get_parent().on_change:
                self.on_change(ConfigChangedEvent(key, self))

    def __repr__(self):
        return str(self.__data)

    def __str__(self):
        return str(self.__data)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __set__(self, obj: any, value: any):
        self.set(obj, value)

    def __get__(self, obj: any, objtype: any):
        return self.get(obj)

    def get(self, key: str, default_value: any = None) -> any:
        """Get a value or a default if not available"""
        return self.__data.get(key, default_value)

    def set(self, key: str, value: any = None):
        """Set a value"""
        if key in self.__data.keys() and self.__data[key] != value:
            self.__changed(key)
        self.__data[key] = value


class ConfigList(list):
    """Extend the base list to trigger when changes happens"""

    def __init__(self, parent: Prop = None):
        super().__init__()
        self.on_change = None
        self.__parent = parent

    def set_callback(self, on_change: Callable[[ConfigChangedEvent], any]):
        """Set a callback to be called when a value changes"""
        self.on_change = on_change

    def get_parent(self):
        """Return the class parent if any"""
        return self.__parent

    def __changed(self, key: any):
        if self.on_change:
            self.on_change(ConfigChangedEvent(key, self))

    def __setitem__(self, index, value):
        self.__changed(index)
        return super().__setitem__(self, index, value)

    def __delitem__(self, i):
        self.__changed(i)
        return super().__delitem__(self, i)


class Config(Prop):
    """Abstract a section of the configuration file"""

    def __init__(self, config: dict, parent: Prop = None):
        super().__init__(parent)
        self.__data = {}
        self.update(config)

    def update(self, src_config: any):
        """Update a configuration tree detecting changes"""

        for key, value in src_config.items():

            if is_value_type(value):
                self.set(key, value)
                continue

            if isinstance(value, list):
                cfglist = ConfigList(self)
                for item in value:
                    cfglist.append(Config(item, cfglist))
                self.set(key, cfglist)
                continue

            self.set(key, Config(value, parent=self))


def is_value_type(value: any) -> bool:
    """Check if the argument is a configuration primitive value"""
    return type(value) in (int, float, bool, str)
