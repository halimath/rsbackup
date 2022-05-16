
import argparse
import os
import sys

from rsbackup import config, create_backup, VERSION_STRING

def main(args):
    """
    main defines the applications CLI entry point. It reads the arguments, loads the configuration and
    dispatches to one of the sub-command handler functions defined below.
    """
    argparser = argparse.ArgumentParser(description='Simple rsync backup')
    argparser.add_argument('-c', '--config-file', dest='config_file', default=os.path.join(os.getenv('HOME'), '.config', 'rsbackup.yaml'), help='Path of the config file')

    subparsers = argparser.add_subparsers(dest='command')

    subparsers.add_parser('list', aliases=('ls',), help='list available configs')
    
    create_initial_parser = subparsers.add_parser('create', aliases=('c',), help='create a backup for a configuration')
    create_initial_parser.add_argument('-m', '--dry-run', dest='dry_run', action='store_true', default=False, help='enable dry run; do not touch any files but output commands instead')
    create_initial_parser.add_argument('--no-link-latest', dest='link_latest', action='store_false', default=True, help='skip linking unchanged files to latest copy (if exists)')
    create_initial_parser.add_argument('config', metavar='CONFIG', type=str, nargs=1, help='name of the config to run')    

    args = argparser.parse_args(args)

    banner()

    cfg = config.load_file(args.config_file)

    if args.command in ('list', 'ls'):
        return list(cfg)

    if args.command in ('create', 'c'):
        return create(cfg, args.config[0], dry_mode=args.dry_run, link_latest=args.link_latest)

    # match args.command:
    #     case 'list' | 'ls':
    #         return list(cfg)
    #     case 'create' | 'c':
    #         return create(cfg, args.config[0], dry_mode=args.dry_run, link_latest=args.link_latest)

def banner():
    print(f"rsbackup v{VERSION_STRING}")
    print('https://github.com/halimath/rsbackup')
    print()

def create(cfg, config_name, dry_mode, link_latest):
    """
    create performs a backup for the named config.
    """
    c = cfg[config_name]
    if not c:
        print(f"{sys.argv[0]}: No backup configuration found: {config_name}", file=sys.stderr)
        return 1

    create_backup(c, dry_mode=dry_mode, out=sys.stdout, link_latest=link_latest)
    return 0

def list(cfg):
    """
    list lists the available backup targets from the configuration.
    """
    for c in cfg:
        print(f'{c.name}{f" - {c.description}" if c.description else ""}')
        print(f'  Source: {c.source}')
        print(f'  Target: {c.target}')
        print('  Excludes:')
        for e in c.excludes:
            print(f'    - {e}')
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))