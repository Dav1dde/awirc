from collections import defaultdict

import awirc.utils

# TODO gevent.spawn for events
# maybe blinker

class EventManager(object):
    def __init__(self, pool):
        self._pool = pool

        self._events = defaultdict(list)

    def bind(self, event_type, handler):
        self._events[event_type.upper()].append(handler)

    def unbind(self, event_type, handler=None):
        event_type = event_type.upper()

        if handler is None:
            self._events[event_type] = list()
        else:
            if handler in self._events[event_type]:
                self._events[event_type].remove(handler)

    def process_event(self, event_type, *args):
        evt_keys = set(awirc.utils.fnmatch_m_s(self._events, event_type))

        for key in evt_keys:
            for handler in self._events[key]:
                self._pool.spawn(handler, event_type, *args)


