from collections import defaultdict
import gevent.pool

from awirc.event import EventManager
from awirc.protocol import Protocol
from awirc.socket import Connection
import awirc.utils


class Client(Connection, EventManager, Protocol):
    def __init__(self, nickname, host, port, ssl=False,
                 username=None, realname=None, password=None):
        self._pool = gevent.pool.Group()

        Connection.__init__(self, self._pool, host, port, ssl=ssl)
        EventManager.__init__(self, self._pool)
        Protocol.__init__(self)

        self.nickname = nickname
        self.username = username or self.nickname
        self.realname = realname or self.nickname
        self.password = password

        self.server_name = None

        # bind intern events!
        for evt, handler in [('001', self.handle_001),
                             ('005', self.handle_005),
                             ('PING', self.handle_pong)]:
            self.bind(evt, handler)

    @property
    def gevent_pool(self):
        return self._pool

    def line_received(self, line):
        self.process_event('RAW_MESSAGE', self.server_name, None, line)

        line = awirc.utils.low_dequote(line.rstrip())
        msg = awirc.utils.parse_line(line)

        if not self.server_name:
            # get the real server name, the server sends the first
            # messages, so we get to know the servers name.
            self.server_name = str(msg.prefix)

        is_chan = False
        if msg.args[0]:
            is_chan = awirc.utils.is_channel(msg.args[0])

        if msg.command == 'NICK' and msg.prefix.nick == self.nickname:
            self.nickname = msg.args[0]

        target = None
        if msg.command in ('NOTICE', 'PRIVMSG'):
            is_priv = msg.command == 'PRIVMSG'
            target = msg.args[0]

            if awirc.utils.X_DELIM in msg.args[1]:
                normal_msgs, extended_msgs = \
                    awirc.utils.extract_ctcp(msg.args[1])
                if extended_msgs:
                    for tag, data in extended_msgs:
                        type_ = 'CTCP_' if is_priv else 'CTCPREPLY_'
                        self.process_event(
                            type_+tag, msg.prefix, target, data
                        )

                if not normal_msgs:
                    return

                msg.args[1] = ' '.join(normal_msgs)

            if is_chan:
                if is_priv:
                    msg.command = 'PUBMSG'
                else:
                    msg.command = 'PUBNOTICE'
            elif not is_priv:
                msg.command = 'PRIVNOTICE'
            #else
            #    msg.command = 'PRIVMSG'

            msg.args = msg.args[1]
        elif msg.command in ('KICK', 'BAN', 'MODE', 'JOIN', 'PART'):
            target = msg.args[0]
            msg.args = msg.args[1:]

        self.process_event(
            msg.command, msg.prefix, target, msg.args
        )

    def disconnect(self, msg=''):
        self.quit(msg)
        self.close()

        self._pool.kill()

    def handle_connect(self):
        self.host, self.port = self._socket.getpeername()

        if self.password:
            self.pass_(self.password)
            self.password = None

        self.nick(self.nickname)
        self.user(self.realname, self.username)

        self.process_event(
            'CONNECT', self.server_name, None, None
        )

    def handle_disconnect(self):
        self.process_event(
            'DISCONNECT', self.server_name, None, None
        )

    def nick(self, newnick):
        super().nick(newnick)
        self.nickname = newnick

    # intern events
    def handle_001(self, event_type, source, target, args):
        self.nickname = args[0]

    def handle_005(self, event_type, source, target, args):
        f, b = awirc.utils.parse_005(args)
        self.rpl_isupport[0].extend(f)
        self.rpl_isupport[1].update(b)

    def handle_pong(self, event_type, source, target, args):
        self.pong(*args[:2])
