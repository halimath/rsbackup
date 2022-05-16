# rsbackup

A simple rsync-based backup solution for unix systems.

`rsbackup` is a simple python application that uses `rsync` to create backups with support for hard links on
incremental backups.

# Installation

TBD

# Usage

`rsbackup` reads backup configurations from a configuration yaml file. The default filename to read is
`$HOME/.config/rsbackup.yaml` but you can specify a different file using the `-c` cli switch.

The config file contains multiple backup configurations. It looks something like this

```yaml
- name: projects
  description: All dev projects
  source: /home/user/projects
  target: /mnt/backup
  excludes:
  - __pycache__/
```

* `name` defines a name for the configuration. This is used as a command line argument to create a backup so
  pick something that needs no shell escaping
* `description` contains an optional description.
* `source` lists the source directory to create a backup of
* `target` contains a target directory which will eventualy contain multiple backups
* `excludes` lists patterns to be excluded from the backup. See `man rsync` for a description of the pattern
  format.

You can use

```shell
rsbackup list
```

to get a list of all backup configurations.

To create a backup, run

```shell
rsbackup create <name of the config>
```

`rsbackup` provides the following command line options

Option | Default Value | Description
-- | -- | --
`-h`, `--help` | - | display a help message
`-c CONFIG_FILE`, `--config-file CONFIG_FILE` | `$HOME/.config/rsbackup.yaml` | path of the config file
`-m`, `--dry-run` | - |  enable dry run; do not touch any files but output commands instead
`--no-link-latest` | - | skip linking unchanged files to latest copy (if exists)

# Development

# License

Copyright 2022 Alexander Metzner.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
