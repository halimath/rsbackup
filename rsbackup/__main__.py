import argparse
import asyncio
import os
import sys
import typing

import tomli

from rsbackup import Backup, __version__

_start_marker = '\033['
_end_marker = 'm'
_separator = ';'
_reset = '0'
_bold = '1'
_default = '22'
_fg_black = '30'
_bg_black = '40'
_fg_red = '31'
_bg_red = '41'
_fg_green = '32'
_bg_green = '42'
_fg_yellow = '33'
_bg_yellow = '43'
_fg_blue = '34'
_bg_blue = '44'
_fg_magenta = '35'
_bg_magenta = '45'
_fg_cyan = '36'
_bg_cyan = '46'
_fg_white = '37'
_bg_white = '47'


def _with_effect(s: str, *effects: str) -> str:
    return _start_marker + _separator.join(effects) + _end_marker + \
        s + _start_marker + _reset + _end_marker


class Output:
    def __init__(self, sink=None, tty=None, tty_width=None):
        self._sink = sink or sys.stdout
        if tty is None and sink is sys.stdout:
            self._tty = sys.stdout.isatty()
            self._tty_width = tty_width or os.get_terminal_size()[0]
        else:
            self._tty = bool(tty)
            self._tty_width = tty_width

        self._progress_written = False

    def print(self, s=None):
        self._clear_progress()

        if s is not None:
            self._sink.write(s)

        self._sink.write('\n')
        self._progress_written = False

    def _print_with_effects(self, s, *effects):
        if self._tty:
            s = _with_effect(s, *effects)
        self.print(s)

    def notify(self, s: str):
        self.print('\u2192\t' + s)

    def info(self, s: str):
        self._print_with_effects(s, _fg_white)

    def warn(self, s: str):
        self._print_with_effects(s, _fg_yellow)

    def error(self, s):
        self._print_with_effects(s, _fg_red)

    def success(self, s):
        self._print_with_effects(s, _fg_green)

    def progress(self, bytes_sent: int, completion: float, eta: str):
        if not self._tty:
            self.print(
                f"{bytes_sent / 1024}KB sent; {completion * 100}%; ETA {eta}")
            return

        self._clear_progress()

        progress_bar_size = min(int(0.8 * self._tty_width) - 14, 100)
        filled = int(completion * progress_bar_size)
        non_filled = progress_bar_size - filled

        self._sink.write(f" [{'=' * filled}{' ' * non_filled}] {eta}")

        self._progress_written = True

    def print_highlight(self, s):
        self._print_with_effects(s, _bold)

    def _clear_progress(self):
        if self._tty and self._progress_written:
            self._sink.write('\b' * self._tty_width)
            self._sink.write(' ' * self._tty_width)
            self._sink.write('\b' * self._tty_width)


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

    output = Output()

    _banner(output)

    cfgs = _load_config_file(args.config_file)

    if args.command in ('list', 'ls'):
        return _list_configs(cfgs, output)

    if args.command in ('create', 'c'):
        return _create_backup(cfgs, args.config[0], dry_mode=args.dry_run,
                              skip_latest=args.skip_latest, output=output)


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


def _banner(output: Output):
    "Shows an application banner to the user."

    output.print_highlight(f"rsbackup v{__version__}")
    output.print('https://github.com/halimath/rsbackup')
    output.print()


def _create_backup(cfgs, config_name, dry_mode, skip_latest, output: Output):
    "Creates a backup for the configuration named config_name."

    try:
        if config_name not in cfgs:
            output.print_error(
                f"No backup configuration found: {config_name}\n")
            return 1

        asyncio.run(cfgs[config_name].run(dry_mode=dry_mode,
                    logger=output, skip_latest=skip_latest))
        return 0
    except Exception as e:
        output.error(f"Error: {e}")
        return 1


def _list_configs(cfgs, output: Output):
    "Lists the available configs to the user."

    for name in cfgs.keys():
        c = cfgs[name]
        output.print_highlight(name)
        if c.description:
            output.print(f" - {c.description}")
        output.print(f'  Source: {c.source}')
        output.print(f'  Target: {c.target}')
        output.print('  Excludes:')
        for e in c.excludes:
            output.print(f'    - {e}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
