from fnmatch import fnmatch
from pprint import pformat
import textwrap

from awirc.protocol import Message


DEBUG = False


# protocol helpers
def parse_line(s):
    prefix = ''
    trailing = []
    if s:
        if s[0] == ':':
            prefix, s = s[1:].split(' ', 1)
        if ' :' in s:
            s, trailing = s.split(' :', 1)
            args = s.split()
            args.append(trailing)
        else:
            args = s.split()
        try:
            command = args.pop(0)
        except IndexError:
            command = ''
        return Message(prefix, command, args)


def parse_005(args):
    relevant = args[1:-1]
    parsed = dict()
    rest = list()
    for d in relevant:
        if '=' in d:
            k, v = d.split('=', 1)
            k = k.upper()
            if k == 'PREFIX':
                v = list(v.replace('(', '').replace(')', ''))
                hlv = int(len(v) / 2) #  python 3: 4/2 = 2.0
                v = dict([v[i::hlv] for i in range(hlv)])
            elif k in ('CHANTYPES', 'STATUSMSG'):
                v = tuple(v)
            elif k in ('CHANMODES', 'CMDS', 'STD'):
                v = tuple(map(get_type, v.split(',')))
            elif k in ('MODES', 'MAXCHANNELS', 'NICKLEN', 'MAXBANS',
                       'TOPICLEN', 'KICKLEN', 'CHANNELLEN', 'CHIDLEN',
                       'SILENCE', 'AWAYLEN', 'WATCH'):
                v = int(v)
            elif k in ('CHANLIMIT', 'MAXLIST', 'IDCHAN', 'TARGMAX'):
                v = dict(map(lambda x: (x[0], get_type(x[1])),
                             [d.split(':') for d in v.split(',')]))
            parsed[k] = v
        else:
            rest.append(d)
    return rest, parsed


# ctcp stuff - http://www.irchelp.org/irchelp/rfc/ctcpspec.html
NUL = chr(0)  # null
LF = chr(0o12)  # newline
NL = LF
CR = chr(0o15)  # carriage return
SPC = chr(0o40)  # space

M_QUOTE = chr(0o20)

# everything has to be escaped with M_QUOTE, even M_QUOTE
M_QUOTE_TABLE = {
    NUL: M_QUOTE + '0',
    NL: M_QUOTE + 'n',
    CR: M_QUOTE + 'r',
    M_QUOTE: M_QUOTE * 2
}
# of course we also need to dequote it
# M_QUOTE
M_DEQUOTE_TABLE = dict([(v, k) for k, v in M_QUOTE_TABLE.items()])


def low_quote(s):
    for c in (M_QUOTE, NUL, NL, CR):  # content of M_QUOTE_TABLE
        s = s.replace(c, M_QUOTE_TABLE[c])
    return s


def low_dequote(s):
    s = iter(s)
    d_s = ''
    for c in s:
        if c == M_QUOTE:
            n = s.next()
            c = M_DEQUOTE_TABLE.get(c+n, n)  # maybe raise an error
        d_s += c
    return d_s

STX = chr(1)  # ctcp marker
X_DELIM = STX

BS = chr(0o134)  # backslash
X_QUOTE = BS

X_QUOTE_TABLE = {
    X_DELIM: X_QUOTE + 'a',
    X_QUOTE: X_QUOTE * 2
}
X_DEQUOTE_TABLE = dict([(v, k) for k, v in X_QUOTE_TABLE.items()])


def ctcp_quote(s):
    for c in (X_QUOTE, X_DELIM):
        s = s.replace(c, X_QUOTE_TABLE[c])
    return s


def ctcp_dequote(s):
    s = iter(s)
    d_s = ''
    for c in s:
        if c == X_QUOTE:
            n = s.next()
            c = X_DEQUOTE_TABLE.get(c+n, n)  # maybe raise an error
        d_s += c
    return d_s


def extract_ctcp(s):
    '''returns a tuple, (normal_msgs, extended_msgs)

    normal_msgs is a list of strings which were not between 2 ctcp delimiter
    extended_msgs is a list of (tag, data) tuples'''
    messages = s.split(X_DELIM)

    normal_msgs = filter(None, messages[::2])
    extended_msgs = list()

    # messages[1::2] = extended_msgs
    # but first let's parse them...
    for e_msg in map(ctcp_dequote, filter(None, messages[1::2])):
        tag = e_msg
        data = None
        if SPC in e_msg:
            tag, data = e_msg.split(SPC, 1)
        extended_msgs.append((tag.upper(), data))

    return normal_msgs, extended_msgs


def make_ctcp_string(messages):
    '''messages is a list containing (tag, data) tuples, data may be None.'''
    msg_buf = list()

    for tag, data in messages:
        if data is not None:
            s = '{} {}'.format(tag.upper(), data)
        else:
            s = tag.upper()
        msg_buf.append(''.join([X_DELIM, ctcp_quote(s), X_DELIM]))

    return ''.join(msg_buf)


# other helpers
def is_channel(target, channel_prefixes='!&#+'):
    'returns True if the target is a channel'
    return target[0] in channel_prefixes


def nick_from_nickmask(prefix):
    'extracts the nick of a nickmask'
    return prefix.split('!')[0]


def userhost_from_nickmask(prefix):
    'extracts the userhost of a nickmask'
    return prefix.split('!')[1]


def user_from_nickmask(prefix):
    'extracts the user of a nickmask'
    return userhost_from_nickmask(prefix).split('@')[0]


def host_from_nickmask(prefix):
    'extracts the host of a nickmask'
    return userhost_from_nickmask(prefix).split('@')[1]


# other helpers
def ssplit(str_, length=420):
    '''splits a string into multiple lines with a given length'''
    buf = list()
    for line in str_.split('\n'):
        buf.extend(textwrap.wrap(line.rstrip('\r'), length))
    return buf


def fnmatch_m_s(iterable, name):
    for s in iterable:
        if fnmatch(name, s):
            yield s


def get_type(val, *types):
    if not types:
        types = (int, float, str)
    for f in types:
        try:
            return f(val)
        except ValueError:
            pass
    return val


def debug(msg, additional=''):
    if DEBUG:
        print('debug ({}): {}'.format((additional), pformat(msg)))


def set_debug(debug=True):
    '''sets debugging, True or False'''
    global DEBUG
    DEBUG = debug
