import argparse

import command.login as LoginCommand
import command.listening as ListeningCommand


def main():
    parser = argparse.ArgumentParser('x2tg')
    subparser = parser.add_subparsers(dest='command')

    login = subparser.add_parser('login')
    login.add_argument('--state-path', type=str, required=True)

    listening = subparser.add_parser('listening')
    listening.add_argument('--state-path', type=str, required=True)
    listening.add_argument('--username', type=str, required=True)

    args = parser.parse_args()
    match args.command:
        case 'login':
            LoginCommand.process(args.state_path)
        case 'listening':
            ListeningCommand.process(args.state_path, args.username)


if __name__ == '__main__':
    main()
