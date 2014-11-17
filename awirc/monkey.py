def _monkey_patch_handle_error(self, context, type, value, tb):
    # https://github.com/gevent/gevent/issues/471
    # just for convenience
    if context is None or issubclass(type, self.SYSTEM_ERROR):
        self.handle_system_error(type, value)
    if not issubclass(type, self.NOT_ERROR):
        self.print_exception(context, type, value, tb)


def patch():
    import gevent.hub
    gevent.hub.Hub.handle_error = _monkey_patch_handle_error
