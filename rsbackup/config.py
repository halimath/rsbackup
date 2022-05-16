from os import path

from collections import namedtuple

import yaml

BackupConfigEntry = namedtuple("Config", "name description source target excludes")

class BackupConfig:
    def __init__(self, *entries):
        self._entries = entries

    def __getitem__(self, name):
        for e in self._entries:
            if e.name == name:
                return e
        return None
    
    def __len__(self):
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries)

def load (stream, basedir='.'):
    """
    load loads the configuration from stream and returns a list of BackupConfig values.
    """
    data = yaml.safe_load(stream)
    
    return BackupConfig(*[BackupConfigEntry(
        entry['name'],
        entry.get('description'),
        path.abspath(path.normpath(entry['source'] if path.isabs(entry['source']) else path.join(basedir, entry['source']))),
        path.abspath(path.normpath(entry['target'] if path.isabs(entry['target']) else path.join(basedir, entry['target']))),
        entry.get('excludes') or [],
    ) for entry in data])

def load_file(name):
    """
    Load configuration from a file named `name` and returns a list of BackupConfig values.
    """
    basedir, _ = path.split(name)
    with open(name, 'r') as file:
        return load(file, basedir)