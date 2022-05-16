
import os
import subprocess
import shutil


class RSync:
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
