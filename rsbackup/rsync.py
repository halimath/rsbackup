
import subprocess
import shutil

class RSync:
    """
    RSync defines a class to execute rsync as a subprocess. The constructor provides keyword args to set
    different options which are passed to rsync as command line args.
    
    source defines the source file or directory.

    target defines the target directory.

    If archive is set to True (the default) rsync is run in archive mode.

    If verbose is set to True (the default) rsync will output additional log.

    If delete is set to True (the default) rsync will be invoked with --delete

    If link_dest is not None it must be string value which points to a directory which is passed to rsync as
    --link-dest. See `man rsync` for an explanation of `--link-dest`.

    If `excludes` is not None it must be an iterable of strings each being given to rsync as `--exclude`.
    See `man rsync` for an explanation of `--exclude` including a formal definition of the pattern syntax
    supported by exclude.

    If `binary` is not None it will be used as the binary to execute rsync, i.e. `/usr/bin/rsync`. If None,
    binary will be determined from the `PATH` environment variable.
    """
    def __init__(self, source, target, archive=True, verbose=True, delete=True, link_dest=None, excludes=None, binary=None):
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
        subprocess.run(self.command, stdin=subprocess.DEVNULL, stdout=log, stderr=log)

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
