from datetime import datetime
from os import path, symlink, makedirs, remove, readlink
import sys

from rsbackup.config import BackupConfigEntry
from rsbackup.rsync import RSync

VERSION = (0, 1, 0)
VERSION_STRING = '.'.join([str(c) for c in VERSION])

_LATEST = '_latest'

def create_backup(cfg: BackupConfigEntry, out=sys.stdout, dry_mode=False, link_latest=True):
    start = datetime.now()
    target = _create_target(cfg, start)
    latest = path.join(cfg.target, _LATEST)
    log_file = path.join(target, '.log')

    print(f"Starting initial backup of '{cfg.name}' at '{start}'", file=out)
    print(f"Writing log to {log_file}", file=out)

    prev = None

    if link_latest and path.exists(latest):
        prev = readlink(latest)
        print(f"Linking unchanged files to {prev} (pointed to by {latest})", file=out)

    rs = RSync(cfg.source, _create_target(cfg, start), excludes=cfg.excludes, link_dest=prev)

    if dry_mode:
        print(file=out)
        print(f"mkdir -p {target}", file=out)
        print(' '.join(rs.command), file=out)
        print(f"rm -f {latest}", file=out)
        print(f"ln -s {target} {latest}", file=out)
        print(file=out)
    else:
        makedirs(target)

        with open(log_file, mode='w') as f:
            print(' '.join(rs.command), file=f)
            rs.run(log=f)
                
        if path.exists(latest):
            remove(latest)
        
        symlink(target, latest)

    end = datetime.now()

    print(f"Backup of '{cfg.name}' finished at '{start}'", file=out)
    print(f"Took {end - start}", file=out)

def _create_target (cfg, ts):
    return path.join(cfg.target, ts.isoformat(sep='_', timespec='seconds').replace(':', '-'))