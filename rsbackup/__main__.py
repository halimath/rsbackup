import argparse
import os
import sys

import tomli

from rsbackup import Backup, __version__


def main(args=None):
    """The main entry point for running rsbackup from the command line.

    main defines the applications CLI entry point. It reads args or sys.argv,
    loads the configuration and dispatches to one of the sub-command handler
    functions defined below.
    """
    argparser = argparse.ArgumentParser(description='Simple rsync backup')
    argparser.add_argument('-c', '--config-file', dest='config_file',
                           default=os.path.join(
                               os.getenv('HOME'), '.config', 'rsbackup.toml'),
                           help='Path of the config file')

    subparsers = argparser.add_subparsers(dest='command')

    subparsers.add_parser('list', aliases=(
        'ls',), help='list available configs')

    create_parser = subparsers.add_parser(
        'create', aliases=('c',), help='create a new generation for the named backup configuration')
    create_parser.add_argument(
        '-m', '--dry-run', dest='dry_run',
        action='store_true', default=False,
        help='enable dry run; do not touch any files but output commands'
    )
    create_parser.add_argument(
        '--skip-latest', dest='skip_latest',
        action='store_true', default=False,
        help='skip linking unchanged files to latest copy (if exists)'
    )
    create_parser.add_argument(
        'config', metavar='CONFIG', type=str, nargs=1,
        help='name of the config to run')

    args = argparser.parse_args(args)

    _banner()

    cfgs = _load_config_file(args.config_file)

    if args.command in ('list', 'ls'):
        return _list_configs(cfgs)

    if args.command in ('create', 'c'):
        return _create_backup(cfgs, args.config[0], dry_mode=args.dry_run,
                              skip_latest=args.skip_latest)


def _load_config(s, basedir='.'):
    """Loads the configuration from the string `s` and returns a dict of 
    Backup values.

    `s` must be valid TOML configuration.
    """
    data = tomli.loads(s)

    return {key: Backup(
        source=os.path.abspath(
            os.path.normpath(data[key]['source'] if os.path.isabs(
                data[key]['source']) else os.path.join(basedir,
                                                       data[key]['source']))),
        target=os.path.abspath(
            os.path.normpath(data[key]['target'] if os.path.isabs(
                data[key]['target']) else os.path.join(basedir,
                                                       data[key]['target']))),
        description=data[key].get('description'),
        excludes=data[key].get('excludes') or [],
    ) for key in data}


def _load_config_file(name):
    """Loads the configuration from a file `name` and returns a dict of
    Backup values.
    """
    basedir, _ = os.path.split(name)
    with open(name, 'r') as file:
        return _load_config(file.read(), basedir)


def _banner():
    "Shows an application banner to the user."

    print(f"rsbackup v{__version__}")
    print('https://github.com/halimath/rsbackup')
    print()


def _create_backup(cfgs, config_name, dry_mode, skip_latest):
    "Creates a backup for the configuration named config_name."

    c = cfgs[config_name]
    if not c:
        print(
            f"{sys.argv[0]}: No backup configuration found: {config_name}",
            file=sys.stderr)
        return 1

    c.run(dry_mode=dry_mode, out=sys.stdout, skip_latest=skip_latest)
    return 0


def _list_configs(cfgs):
    "Lists the available configs to the user."
    for name in cfgs.keys():
        c = cfgs[name]
        print(f'{name}{f" - {c.description}" if c.description else ""}')
        print(f'  Source: {c.source}')
        print(f'  Target: {c.target}')
        print('  Excludes:')
        for e in c.excludes:
            print(f'    - {e}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
