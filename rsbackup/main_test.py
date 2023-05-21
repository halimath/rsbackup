from rsbackup.__main__ import _load_config
from rsbackup import Backup


def test_load_config():
    input = """
[test]
description = 'A backup configuration for tests'
sources = ['/spam/eggs/backup']
target = '/spam/eggs/tmp'
excludes = [
    '__pycache__/',
]

[another_test]
sources = ['/home']
target = '/mnt/backups/homes'
excludes = [
    'dummy',
    'foo',
    '.cache',
]
    """
    c = _load_config(input, '/spam/eggs')
    assert 2 == len(c)
    assert Backup(
        description='A backup configuration for tests',
        sources=['/spam/eggs/backup'],
        target='/spam/eggs/tmp',
        excludes=['__pycache__/']) == c['test']
    assert Backup(
        description=None,
        sources=['/home'],
        target='/mnt/backups/homes',
        excludes=['dummy', 'foo', '.cache']) == c['another_test']
