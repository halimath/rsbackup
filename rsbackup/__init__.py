"""rsbackup is a python module which wraps the `rsync` command to create 
file system backups on unix systems that feature

1. multiple generations
1. hardlinks to save disk space for unchanged files

rsbackup is primary designed for being run from the command line but it can
also be incorporated into other applications by using the functionality 
exported from this module.
"""

import datetime
import os
import shutil
import subprocess
import sys

__version__ = '0.1.2'
__author__ = 'Alexander Metzner'

_LATEST = '_latest'


class Backup:
    """A class that represents a single backup definition.

    A Backup can be exectued which will produce a new backup generation. 
    """

    def __init__(self, source, target, description=None, excludes=None):
        """Initializes the Backup instance to use.
        
        `source` is the source path to create a backup from.

        `target` is the target path containing the backup generations.

        `description` is an optional human readable description.

        `excludes` is an optional list of exclude patterns as defined by
        rsync.
        """
        self.source = source
        self.target = target
        self.description = description
        self.excludes = excludes or []

    def __eq__(self, other):
        return self.source == other.source and\
            self.target == other.target and\
                self.description == other.description and\
                    self.excludes == other.excludes

    def run(self, out=sys.stdout, dry_mode=False, skip_latest=False):
        """Creates a new generation for this backup.

        Output is written to `out`.

        If `dry_mode` is set to `True`, no file system operations will be
        executed and corresponding shell commands will be printed to `out`.
        Note that these commands only demonstrate what would be done. Only
        rsync will be executed directly. All other operations will be carried
        out using python library calls.

        If `skip_latest` is set to `True`, no `_latest` symlink will be used
        to create hard links for unchanged files and the link will not be
        updated after the operation.
        """
        start = datetime.datetime.now()
        target = os.path.join(self.target, start.isoformat(
            sep='_', timespec='seconds').replace(':', '-'))
        latest = os.path.join(self.target, _LATEST)
        log_file = os.path.join(target, '.log')

        print(
            f"Creating new backup generation for '{self.source}' at '{start}'",
            file=out)
        print(f"Saving log to {log_file}", file=out)

        prev = None

        if not skip_latest and os.path.exists(latest):
            prev = os.readlink(latest)
            print(
                f"Linking unchanged files to {prev} (defined by {latest})",
                file=out)

        rs = RSync(self.source, target, excludes=self.excludes, link_dest=prev)

        if dry_mode:
            print('dry_mode is set to True; not going to touch any files.\n',
                  file=out)
            print(f"mkdir -p {target}", file=out)
            print(' '.join(rs.command), file=out)

            if not skip_latest:
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

        print(f"Backup of '{self.source}' finished at '{start}'", file=out)
        print(f"Took {end - start}", file=out)


class RSync:
    """A class to execute rsync as a subprocess. The constructor provides 
    keyword args to set different options which are passed to rsync as command
    line args.

    `source` defines the source file or directory.

    `target` defines the target directory.

    If `archive` is set to True (the default) rsync is run in archive mode.

    If `verbose` is set to True (the default) rsync will output additional log.

    If `delete` is set to `True` (the default) rsync will be invoked with 
    `--delete`.

    If `link_dest` is not `None` it must be string value which points to a
    directory which is passed to rsync as `--link-dest`. See the documentation
    for rsync for an explanation of `--link-dest`.

    If `excludes` is not `None` it must be an iterable of strings each being
    given to rsync as `--exclude`. See the rsync documentation for an
    explanation of `--exclude` including a formal definition of the pattern
    syntax supported by exclude.

    If `binary` is not `None` it will be used as the binary to execute rsync,
    i.e. `/usr/bin/rsync`. If `None`, binary will be determined from the `PATH`
    environment variable.
    """

    def __init__(self, source, target, archive=True, verbose=True, delete=True,
                 link_dest=None, excludes=None, binary=None):
        self.source = source
        self.target = target
        self.archive = archive
        self.verbose = verbose
        self.delete = delete
        self.link_dest = link_dest
        self.excludes = excludes
        self.binary = binary or shutil.which('rsync')

    def run(self, log=None):
        if not log:
            log = subprocess.DEVNULL
        subprocess.run(self.command, stdin=subprocess.DEVNULL,
                       stdout=log, stderr=log)

    def _args(self):
        args = []
        if self.archive:
            args.append('-a')
        if self.verbose:
            args.append('-v')
        if self.delete:
            args.append('--delete')
        args.append(self.source)
        if self.link_dest:
            args.append('--link-dest')
            args.append(self.link_dest)
        if self.excludes:
            for exclude in self.excludes:
                args.append(f"--exclude={exclude}")
        args.append(self.target)

        return args

    @property
    def command(self):
        return [self.binary] + self._args()
