from collections import defaultdict
from abc import ABCMeta, abstractclassmethod

import awirc.utils


class Prefix(object):
    def __init__(self, prefix):
        self.nick = None
        self.user = None
        self.host = None

        if '!' in prefix:
            self.nick = awirc.utils.nick_from_nickmask(prefix)
            self.user = awirc.utils.user_from_nickmask(prefix)
            self.host = awirc.utils.host_from_nickmask(prefix)
        else:
            self.host = prefix

    def __str__(self):
        if self.nick is not None and self.user is not None:
            return '{}!{}@{}'.format(self.nick, self.user, self.host)
        else:
            return self.host

    def __repr__(self):
        return 'IRCPrefix(nick={!r}, user={!r}, host={!r})'.format(
            self.nick, self.user, self.host
        )


class Message(object):
    def __init__(self, prefix, command, args):
        self.prefix = Prefix(prefix)
        self.command = command.upper()
        self.args = args

    def __getitem__(self, key):
        return (self.prefix, self.command, self.args).__getitem__(key)

    def __contains__(self, item):
        return (self.prefix, self.command, self.args).__contains__(item)

    def __str__(self):
        return ' '.join([str(self.prefix), self.command, ' '.join(self.args)])

    def __repr__(self):
        return 'Message(prefix={}, command={!r}, args={!r})'.format(
            self.prefix, self.command, self.args
        )


class Protocol(metaclass=ABCMeta):
    def __init__(self):
        self.rpl_isupport = (list(), defaultdict(tuple))

    def action(self, target, action):
        self.ctcp(target, (('ACTION', action),))

    def admin(self, server=''):
        self.send('ADMIN {}'.format(server))

    def ctcp(self, target, messages):
        '''sends a ctcp request to target.

        messages is a list containing (tag, data) tuples,
        data may be None.'''
        self.privmsg(target, awirc.utils.make_ctcp_string(messages))

    def ctcp_reply(self, target, messages):
        '''sends a ctcp reply to target.

        messages is a list containing (tag, data) tuples,
        data may be None.'''
        self.notice(target, awirc.utils.make_ctcp_string(messages))

    def globops(self, text):
        self.send('GLOBOPS :{}'.format(text))

    def info(self, server=''):
        self.send('INFO {}'.format(server))

    def invite(self, nick, channel):
        self.send('INVITE {} {}'.format(nick, channel))

    def ison(self, nicks):
        self.send('ISON {}'.format(' '.join(nicks)))

    def join_channel(self, channel, key=''):
        chans = [i.strip() for i in channel.split(',')]
        chanp = False
        for chan in chans:
            if chan:
                if hasattr(self, 'rpl_isupport'):
                    chanp = self.rpl_isupport[1]['CHANTYPES']
                if not chanp:
                    chanp = '!&#+'
                if not chan[0] in chanp:
                    chan = '#' + chan
                self.send('JOIN {} {}'.format(chan, key))

    def kick(self, channel, nick, comment=''):
        self.send('KICK {} {} :{}'.format(channel, nick, comment))

    def links(self, server_mask, remote_server=''):
        cmd = 'LINKS'
        if remote_server:
            cmd += ' ' + remote_server
        cmd += ' ' + server_mask
        self.send(cmd)

    def list(self, channels=None, server=''):
        cmd = 'LIST'
        if channels is not None:
            cmd = 'LIST {}'.format(','.join(channels))
        cmd += ' ' + server
        self.send(cmd)

    def lusers(self, server=''):
        self.send('LUSERS {}'.format(server))

    def mode(self, channel, mode, user=''):
        self.send('MODE {} {} {}'.format(channel, mode, user))

    def motd(self, server=''):
        self.send('MOTD {}'.format(server))

    def names(self, channel=''):
        self.send('NAMES {}'.format(channel))

    def nick(self, newnick):
        self.send('NICK {}'.format(newnick))

    def notice(self, target, text):
        for part in awirc.utils.ssplit(text, 420):
            self.send('NOTICE {} :{}'.format(
                target, ''.join(filter(None, part)))
            )

    def oper(self, nick, password):
        self.send('OPER {} {}'.format(nick, password))

    def part(self, channel, message=''):
        self.send('PART {} {}'.format(channel, message))

    def pass_(self, password):
        self.send('PASS {}'.format(password))

    def ping(self, target, target2=''):
        self.send('PING {} {}'.format(target, target2))

    def pong(self, target, target2=''):
        self.send('PONG {} {}'.format(target, target2))

    def privmsg(self, target, text):
        for part in awirc.utils.ssplit(text, 420):
            self.send('PRIVMSG {} :{}'.format(
                target, ''.join(filter(None, part)))
            )

    def privmsg_many(self, targets, text):
        for part in awirc.utils.ssplit(text, 420):
            self.send('PRIVMSG {} :{}'.format(
                ','.join(targets), ''.join(filter(None, part))))

    def quit(self, message=''):
        self.send('QUIT :{}'.format(message))

    def squit(self, server, comment=''):
        self.send('SQUIT {} :{}'.format(server, comment))

    def stats(self, statstype, server=''):
        self.send('STATS {} {}'.format(statstype, server))

    def time(self, server=''):
        self.send('TIME {}'.format(server))

    def topic(self, channel, new_topic=None):
        if new_topic is None:
            self.send('TOPIC {}'.format(channel))
        else:
            self.send('TOPIC {} :{}'.format(channel, new_topic))

    def trace(self, target=''):
        self.send('TRACE {}'.format(target))

    def user(self, username, realname):
        self.send('USER {} 0 * :{}'.format(username, realname))

    def userhost(self, nick):
        self.send('USERHOST {}'.format(nick))

    def users(self, server=''):
        self.send('USERS {}'.format(server))

    def version(self, server=''):
        self.send('VERSION {}'.format(server))

    def wallops(self, text):
        self.send('WALLOPS :{}'.format(text))

    def who(self, target, op=''):
        self.send('WHO {} {}'.format(target, op))

    def whois(self, target):
        self.send('WHOIS {}'.format(target))

    def whowas(self, nick, max='', server=''):
        self.send('WHOWAS {} {} {}'.format(nick, max, server))

    @abstractclassmethod
    def send(self, msg):
        raise NotImplementedError

# TODO IRCv3

