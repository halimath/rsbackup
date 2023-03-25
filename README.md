# rsbackup

[![CI Status](https://github.com/halimath/rsbackup/workflows/CI/badge.svg)](https://github.com/halimath/rsbackup/actions/workflows/ci.yaml)
[![Releases](https://img.shields.io/github/v/release/halimath/rsbackup.svg)](https://github.com/halimath/rsbackup/releases)
[![PyPi](https://img.shields.io/pypi/v/rsbackup.svg)](https://pypi.org/project/rsbackup/)
[![Wheel](https://img.shields.io/pypi/wheel/rsbackup.svg)](https://pypi.org/project/rsbackup/)
[![Python Versions](https://img.shields.io/pypi/pyversions/rsbackup.svg)](https://pypi.org/project/rsbackup/)

A simple rsync-based backup solution for unix systems.

`rsbackup` is a simple python application that uses `rsync` to create backups with support for hard links on
incremental backups.

# Installation

`rsbackup` requires a working installation of Python 3.10 and the `rsync` command line tool. `rsbackup` uses only `rsync` flags
supported on both Linux and BSD versions (i.e. MacOS) of `rsync`.

Use the following command to install `rsbackup`:

```shell
pip install rsbackup
```

# Usage

`rsbackup` reads backup configurations from a configuration [TOML](https://toml.io/en/) file. The default 
filename to read is `$HOME/.config/rsbackup.toml` but you can specify a different file using the `-c` cli 
switch.

The config file contains multiple backup configurations. It looks something like this

```toml
[projects]
description = 'All dev projects'
source = '/home/user/projects'
target = '/mnt/backup'
excludes = [
  '__pycache__/',
]
```

See [`rsbackup.toml`](./rsbackup.toml) for a documented example.

Each TOML `table` (i.e. each section header) defines a single backup configuration. The header contains
the config's name. This is used as a command line argument to create a backup so pick something that needs no
shell escaping.

Each table contains the following keys:

Key | Type | Optional | Description
-- | -- | -- | --
`description` | string | yes | contains an optional description.
`source` | string | no | lists the source directory to create a backup of
`target` | string | no | contains a target directory which will eventualy contain multiple backups
`excludes` | array of strings | yes | lists patterns to be excluded from the backup. See the `rsync` documentation for a description of the pattern format.

You can use

```shell
rsbackup list
```

to get a list of all backup configurations.

To create a backup, run

```shell
rsbackup create <name of the config>
```

This will create a new directory named after the timestamp (in seconds) inside the target to contain the
backup. 

If you run `rsbackup create` with the testconfiguration provided in [`rsbackup.toml`](./rsbackup.toml) you
will get the following backup under `tmp`:

```
tmp
├── 2022-05-19_15-08-25
│   └── rsbackup
│       ├── config.py
│       ├── config_test.py
│       ├── __init__.py
│       ├── __main__.py
│       ├── rsbackup_test.py
│       ├── rsync.py
│       └── rsync_test.py
└── _latest -> /home/alex/Development/python/backup/tmp/2022-05-19_15-08-25
```

Of course, the name of the backup directory will depend on the local time you execute the backup. Notice that
no `__pycache__` directory is contained in the backup as it is excluded. 

`rsbackup` provides the following command line options

Option | Default Value | Description
-- | -- | --
`-h`, `--help` | - | display a help message
`-c CONFIG_FILE`, `--config-file CONFIG_FILE` | `$HOME/.config/rsbackup.yaml` | path of the config file
`-m`, `--dry-run` | - |  enable dry run; do not touch any files but output commands instead
`--no-link-latest` | - | skip linking unchanged files to latest copy (if exists)

# Development

You need Python >= 3.9 to run and thus develop. `tomli` is used to load TOML files. `pytest` is used to 
execute unit and acceptance tests. `setuptools` is used as a [PEP517](https://peps.python.org/pep-0517/)
build backend. 

`requirements.txt` only contains the minimal set of dependencies to install the application, so it only 
contains `tomli`.

# License

Copyright 2022, 2023 Alexander Metzner.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
