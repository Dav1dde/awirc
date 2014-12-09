import gevent.socket
import gevent.queue
import gevent.event
import gevent.pool
import gevent.ssl
import gevent

import awirc.utils


class Connection(object):
    def __init__(self, pool, host, port, ssl=False):
        self._pool = pool

        self.host = host
        self.port = port
        self.ssl = ssl

        self._socket = None

        self._chunk_size = 4096

        self._connected = False
        self._out_queue = gevent.queue.Queue()

    def connect(self, timeout=10, source=None, ssl_args=None):
        if ssl_args is None:
            ssl_args = dict()

        self._socket = gevent.socket.create_connection(
            (self.host, self.port),
            timeout=timeout,
            source_address=source
        )

        if self.ssl:
            self._socket = gevent.ssl.wrap_socket(self._socket, **ssl_args)

        gevent.socket.wait_write(self._socket.fileno(), timeout=timeout)
        read = self._pool.spawn(self._read)
        # the read greenlet exits (e.g. other end closes connection, timeout)
        # but the write greenlet will still wait for information
        read.link(lambda g: self.terminate())
        self._pool.spawn(self._write)

        self.handle_connect()

    def _read(self):
        buffer = ''

        while True:
            gevent.socket.wait_read(self._socket.fileno())

            incoming = ''
            try:
                incoming = self._socket.recv(self._chunk_size)
            except ConnectionError:
                pass

            if not incoming:
                break

            try:
                incoming = incoming.decode('utf-8')
            except UnicodeDecodeError:
                incoming = incoming.decode('iso-8859-1', errors='ignore')

            buffer += incoming
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)

                self._pool.spawn(self.line_received, line.strip())

        self.handle_disconnect()

    def _write(self):
        while True:
            message = self._out_queue.get()
            self._socket.sendall(message)

    def send(self, data):
        message = awirc.utils.low_quote(data)

        if not message.endswith('\r\n'):
            message = '{}\r\n'.format(message)

        message = message.encode('utf-8')

        self._out_queue.put(message)

    def terminate(self, block=True, timeout=None):
        try:
            self._socket.shutdown(gevent.socket.SHUT_RDWR)
            self._socket.close()
        except OSError:
            # Connection already down
            pass

        self._pool.kill(block=block, timeout=timeout)

    def handle_connect(self):
        pass

    def handle_disconnect(self):
        pass
