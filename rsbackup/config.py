from os import path

from collections import namedtuple

import tomli

BackupConfigEntry = namedtuple("Config", "name description source target excludes")

def loads (s, basedir='.'):
    "Loads the configuration from s and returns a dict of BackupConfigEntry values."
    data = tomli.loads(s)
    
    return {key: BackupConfigEntry(
        key,
        data[key].get('description'),
        path.abspath(path.normpath(data[key]['source'] if path.isabs(data[key]['source']) else path.join(basedir, data[key]['source']))),
        path.abspath(path.normpath(data[key]['target'] if path.isabs(data[key]['target']) else path.join(basedir, data[key]['target']))),
        data[key].get('excludes') or [],
    ) for key in data}

def load_file(name):
    "Loads configuration from a file name and returns a dict of BackupConfigEntry values."
    basedir, _ = path.split(name)
    with open(name, 'r') as file:
        return loads(file.read(), basedir)