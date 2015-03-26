import collections


class Dispatcher(collections.MutableMapping):
    def __init__(self, prototype, prefix='do'):
        self.method_map = dict()
        self._setup_dispatcher(prototype, prefix)

    def __getitem__(self, key):
        return self.method_map[key]

    def __setitem__(self, key, value):
        self.method_map[key] = value

    def __delitem__(self, key):
        del self.method_map[key]

    def __len__(self):
        return len(self.method_map)

    def __iter__(self):
        return iter(self.method_map)

    def __repr__(self):
        return repr(self.method_map)

    def _prefix_callables(self, prototype, prefix):
        names = [name for name in dir(prototype) if name.startswith(prefix)]
        attrs = [getattr(prototype, name) for name in names]
        callables = [attr for attr in attrs if callable(attr)]
        return callables

    def _setup_dispatcher(self, prototype, prefix):
        callables = self._prefix_callables(prototype, prefix)

        for method in callables:
            name = method.__name__[2:]
            self[name] = method
