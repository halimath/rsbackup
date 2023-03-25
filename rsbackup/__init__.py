"""rsbackup is a python module which wraps the `rsync` command to create 
file system backups on unix systems that feature

1. multiple generations
1. hardlinks to save disk space for unchanged files

rsbackup is primary designed for being run from the command line but it can
also be incorporated into other applications by using the functionality 
exported from this module.
"""

import asyncio
import datetime
import os
import shutil
import typing

import aiofiles
import aiofiles.os

__version__ = '0.3.0'
__author__ = 'Alexander Metzner'

_LATEST = '_latest'


class LoggingProtocol(typing.Protocol):
    """
    A typing definition for objects that can handle logging output for the
    backup process.

    ``info`` and ``warn`` will be called to report important events in the backup
    procedure.

    ``details`` will be called to notify on additional details of the backup
    creation (such as generated timestamps).

    ``start_progress``, ``stop_progress`` and ``update_progress`` will be 
    called to signal start and stop of a progress monitoring as well as updates
    of the current progress.    
    """

    async def details(self, s: str): ...

    async def info(self, s: str): ...
    async def success(self, s: str): ...
    async def warn(self, s: str): ...

    async def start_progress(self): ...
    async def stop_progress(self): ...


class Backup:
    """A class that represents a single backup definition.

    A Backup can be exectued which will produce a new backup generation. 
    """

    def __init__(self, source: str, target: str,
                 description: typing.Optional[str] = None,
                 excludes: typing.Optional[typing.Iterable[str]] = None):
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
        self.excludes = list(excludes or [])

    def __eq__(self, other):
        return self.source == other.source and\
            self.target == other.target and\
            self.description == other.description and\
            self.excludes == other.excludes

    async def run(self, logger: typing.Optional[LoggingProtocol] = None,
                  dry_mode: bool = False, skip_latest: bool = False):
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

        await logger.info(f"Creating new backup generation for '{self.source}'")

        await logger.details(f"Creating backup at {target}")

        prev = None

        if not skip_latest and os.path.exists(latest):
            prev = os.readlink(latest)
            await logger.info(
                f"Found previous backup generation at {prev}")

        rs = RSync(self.source, target, excludes=self.excludes, link_dest=prev)

        if dry_mode:
            await logger.warn(
                'dry_mode is set to True; not going to touch any files.')
            await logger.details(f"mkdir -p {target}")
            await logger.details(' '.join(rs.command))

            await logger.start_progress()
            rsync_exit_code = await rs.run(log=None, dry_run=True)
            await logger.stop_progress()

            if rsync_exit_code != 0:
                raise ValueError(
                    f"rsync returned unexpected exit code {rsync_exit_code}.")

            if not skip_latest:
                await logger.details(f"rm -f {latest}")
                await logger.details(f"ln -s {target} {latest}")
        else:            
            await aiofiles.os.makedirs(target)

            async with aiofiles.open(log_file, mode='w') as f:
                await logger.info('Starting rsync')
                await logger.details(f"writing output to {log_file}")

                await logger.start_progress()
                rsync_exit_code = await rs.run(log=f)
                await logger.stop_progress()
                if rsync_exit_code != 0:
                    raise ValueError(
                        f"rsync returned unexpected exit code {rsync_exit_code}.")

                await logger.details('rsync finished')

            if await aiofiles.os.path.exists(latest):
                await aiofiles.os.remove(latest)

            # TODO: Make this asynchronous
            os.symlink(target, latest)

        end = datetime.datetime.now()

        await logger.success(f"Backup of '{self.source}' finished at '{start}'")
        await logger.details(f"Took {end - start}")


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

    def __init__(self, source: str, target: str, archive: bool = True,
                 verbose: bool = True, delete: bool = True,
                 link_dest: str = None,
                 excludes: typing.Optional[typing.Iterable[str]] = None,
                 binary: typing.Optional[str] = None):
        self.source = source
        self.target = target
        self.archive = archive
        self.verbose = verbose
        self.delete = delete
        self.link_dest = link_dest
        self.excludes = excludes
        self.binary = binary or shutil.which('rsync')

    async def run(self,
                  log=None,
                  dry_run=False):
        """
        runs the configured rsync process asyncroniously.

        Returns a coroutine that when awaited produces rsync's exit code.

        `log` can be an `write`able to write log output to. If `None` log is
        silently discarded.
        """

        p = await asyncio.create_subprocess_exec(
            self.binary,
            *self._args(dry_run=dry_run),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            stdin=asyncio.subprocess.DEVNULL,
            env={
                'LC_NUMERIC': 'en.US',
            }
            # limit=2**32,
        )

        while True:
            data = await p.stdout.readuntil()
            line = data.decode('ascii').rstrip()
            if not line:
                break

            await log.write(line + '\n')

        return await p.wait()

    def _args(self, dry_run=False):
        args = []

        if self.archive:
            args.append('--archive')

        if self.verbose:
            args.append('--verbose')

        if self.delete:
            args.append('--delete')

        if dry_run:
            args.append('--dry-run')

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
