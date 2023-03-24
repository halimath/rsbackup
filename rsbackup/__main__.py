import argparse
import asyncio
import os
import platform
import sys

import tomli

from termapp.styles import BOLD, FG_CYAN
from termapp.asyncio import AppProtocol, create_app
from rsbackup import Backup, LoggingProtocol, __version__


class AppLoggingProtocolAdapter(LoggingProtocol):
    def __init__(self, app: AppProtocol):
        self._app = app

    async def details(self, s: str):
        await self._app.details(s)

    async def info(self, s: str):
        await self._app.info(s)

    async def success(self, s: str):
        await self._app.success(s)

    async def warn(self, s: str):
        await self._app.info(s)

    async def start_progress(self):
        await self._app.start_progress(show_completion=False)

    async def stop_progress(self):
        await self._app.stop_progress()


def config_file_path(file_name: str) -> str:
    match platform.system():
        case 'Darwin':
            return os.path.join(os.getenv('HOME'), 'Library', 'Preferences', file_name)
        case _:
            return os.path.join(os.getenv('HOME'), '.config', file_name)


def main(args=None):
    """The main entry point for running rsbackup from the command line.

    main defines the applications CLI entry point. It reads args or sys.argv,
    loads the configuration and dispatches to one of the sub-command handler
    functions defined below.
    """
    argparser = argparse.ArgumentParser(description='Simple rsync backup')
    argparser.add_argument('-c', '--config-file', dest='config_file',
                           default=config_file_path('rsbackup.toml'),
                           help='Path of the config file')

    subparsers = argparser.add_subparsers(dest='command')

    subparsers.add_parser('list', aliases=(
        'ls',), help='list available configs')

    create_parser = subparsers.add_parser(
        'create', aliases=('c',),
        help='create a new generation for the named backup configuration')
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

    cfgs = _load_config_file(args.config_file)

    app = create_app()

    async def _main():
        await _banner(app)

        if args.command in ('list', 'ls'):
            return await _list_configs(cfgs, app)

        if args.command in ('create', 'c'):
            return await _create_backup(cfgs, args.config[0], dry_mode=args.dry_run,
                                        skip_latest=args.skip_latest, app=app)

    return asyncio.run(_main())
    


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


async def _banner(app: AppProtocol):
    "Shows an application banner to the user."

    await app.write_line(f"rsbackup v{__version__}", BOLD)
    await app.write_line('https://github.com/halimath/rsbackup')
    await app.write_line()


async def _create_backup(cfgs, config_name, dry_mode, skip_latest, app: AppProtocol):
    "Creates a backup for the configuration named config_name."

    try:
        if config_name not in cfgs:
            await app.danger(
                f"No backup configuration found: {config_name}\n")
            return 1

        await cfgs[config_name].run(dry_mode=dry_mode,
                    logger=AppLoggingProtocolAdapter(app), skip_latest=skip_latest)
        return 0
    except Exception as e:
        await app.danger(f"Error: {e}")
        return 1


async def _list_configs(cfgs, app: AppProtocol):
    "Lists the available configs to the user."

    for name in cfgs.keys():
        c = cfgs[name]
        async with app.apply_styles(BOLD, FG_CYAN):
            await app.write(name)
        if c.description:
            await app.write(f" - {c.description}")

        await app.write_line()
        
        await app.write('  Source: ')
        async with app.apply_styles(FG_CYAN):
            await app.write_line(c.source)

        await app.write('  Target: ')
        async with app.apply_styles(FG_CYAN):
            await app.write_line(c.target)

        await app.write_line('  Excludes:')
        for e in c.excludes:
            await app.write_line(f'    - {e}')
        await app.write_line()
    return 0


if __name__ == '__main__':
    sys.exit(main())
