import asyncio
import argparse

import command.login as LoginCommand
import command.serve as ServeCommand

_handler = {'login': LoginCommand, 'serve': ServeCommand}


def setup():
    parser = argparse.ArgumentParser('x2tg')

    subparser = parser.add_subparsers(dest='command')

    login = subparser.add_parser('login')
    login.add_argument('--browser-context', type=str, required=True)

    serve = subparser.add_parser('serve')
    serve.add_argument('--browser-context', type=str, required=True)
    serve.add_argument('--username', type=str, required=True)
    serve.add_argument('--bot-token', type=str, required=True)
    serve.add_argument('--chat-id', type=str, required=True)

    return parser


def main():
    args = setup().parse_args()
    handler = _handler[args.command]

    args = vars(args)
    args.pop('command')
    asyncio.run(handler.process(**args))


if __name__ == '__main__':
    main()
