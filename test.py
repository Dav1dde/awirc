import awirc

import random

def debug_message(type, source, target, client, args):
    if type == 'RAW_MESSAGE':
        return

    print(type, '\t', source, target, args)


def main():
    c = awirc.Client(
        'awircbot{}'.format(random.randint(0, 9999)),
        'chat.freenode.net', port=6667
    )
    c.bind('*', debug_message)
    c.connect()

    c.worker.join()


if __name__ == '__main__':
    main()
