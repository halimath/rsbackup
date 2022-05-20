import argparse
import datetime
import os
import sys

from rsbackup.config import BackupConfigEntry, load_file
from rsbackup.rsync import RSync

__version__ = '0.1.2'
__author__ = 'Alexander Metzner'

_LATEST = '_latest'

def create_backup(cfg: BackupConfigEntry, out=sys.stdout, dry_mode=False, link_latest=True):
    """
    create_backup executes the backup process for the given configuration cfg. It logs output to out.
    
    If dry_mode is set to True, no file system operations will be executed and corresponding shell commands
    will be printed to out. Note that these commands only demonstrates what would be done. Only rsync will
    be executed directly. All other operations will be done using python library calls.

    If link_latest is set to False, no _latest symlink will be used to create hard links for unchanged files
    and the link will not be updated after the operation.
    """
    start = datetime.datetime.now()
    target = os.path.join(cfg.target, start.isoformat(sep='_', timespec='seconds').replace(':', '-'))
    latest = os.path.join(cfg.target, _LATEST)
    log_file = os.path.join(target, '.log')

    print(f"Starting initial backup of '{cfg.name}' at '{start}'", file=out)
    print(f"Writing log to {log_file}", file=out)

    prev = None

    if link_latest and os.path.exists(latest):
        prev = os.readlink(latest)
        print(f"Linking unchanged files to {prev} (pointed to by {latest})", file=out)

    rs = RSync(cfg.source, target, excludes=cfg.excludes, link_dest=prev)

    if dry_mode:
        print(file=out)
        print(f"mkdir -p {target}", file=out)
        print(' '.join(rs.command), file=out)
        print(f"rm -f {latest}", file=out)
        print(f"ln -s {target} {latest}", file=out)
        print(file=out)
    else:
        os.makedirs(target)

        with open(log_file, mode='w') as f:
            print(' '.join(rs.command), file=f)
            rs.run(log=f)
                
        if os.path.exists(latest):
            os.remove(latest)
        
        os.symlink(target, latest)

    end = datetime.datetime.now()

    print(f"Backup of '{cfg.name}' finished at '{start}'", file=out)
    print(f"Took {end - start}", file=out)


def main(args=None):
    """
    main defines the applications CLI entry point. It reads args or sys.argv, loads the configuration and
    dispatches to one of the sub-command handler functions defined below.
    """
    argparser = argparse.ArgumentParser(description='Simple rsync backup')
    argparser.add_argument('-c', '--config-file', dest='config_file', default=os.path.join(os.getenv('HOME'), '.config', 'rsbackup.toml'), help='Path of the config file')

    subparsers = argparser.add_subparsers(dest='command')

    subparsers.add_parser('list', aliases=('ls',), help='list available configs')
    
    create_initial_parser = subparsers.add_parser('create', aliases=('c',), help='create a backup for a configuration')
    create_initial_parser.add_argument('-m', '--dry-run', dest='dry_run', action='store_true', default=False, help='enable dry run; do not touch any files but output commands instead')
    create_initial_parser.add_argument('--no-link-latest', dest='link_latest', action='store_false', default=True, help='skip linking unchanged files to latest copy (if exists)')
    create_initial_parser.add_argument('config', metavar='CONFIG', type=str, nargs=1, help='name of the config to run')    

    args = argparser.parse_args(args)

    _banner()

    cfgs = load_file(args.config_file)

    if args.command in ('list', 'ls'):
        return _list_configs(cfgs)

    if args.command in ('create', 'c'):
        return _create_backup(cfgs, args.config[0], dry_mode=args.dry_run, link_latest=args.link_latest)

    # match args.command:
    #     case 'list' | 'ls':
    #         return list(cfg)
    #     case 'create' | 'c':
    #         return create(cfg, args.config[0], dry_mode=args.dry_run, link_latest=args.link_latest)

def _banner():
    "Shows an application banner to the user."

    print(f"rsbackup v{__version__}")
    print('https://github.com/halimath/rsbackup')
    print()

def _create_backup(cfgs, config_name, dry_mode, link_latest):
    "Creates a backup for the configuration named config_name."
    
    c = cfgs[config_name]
    if not c:
        print(f"{sys.argv[0]}: No backup configuration found: {config_name}", file=sys.stderr)
        return 1

    create_backup(c, dry_mode=dry_mode, out=sys.stdout, link_latest=link_latest)
    return 0

def _list_configs(cfgs):
    "Lists the available configs to the user."
    for c in cfgs.values():
        print(f'{c.name}{f" - {c.description}" if c.description else ""}')
        print(f'  Source: {c.source}')
        print(f'  Target: {c.target}')
        print('  Excludes:')
        for e in c.excludes:
            print(f'    - {e}')
    return 0    