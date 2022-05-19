from rsbackup.config import loads, BackupConfigEntry

def test_load ():
    input = """
[test]
description = 'A backup configuration for tests'
source = '/spam/eggs/backup'
target = '/spam/eggs/tmp'
excludes = [
    '__pycache__/',
]

[another_test]
source = '/home'
target = '/mnt/backups/homes'
excludes = [
    'dummy',
    'foo',
    '.cache',
]
    """
    c = loads(input, '/spam/eggs')
    assert 2 == len(c)
    assert BackupConfigEntry('test', 'A backup configuration for tests', '/spam/eggs/backup', '/spam/eggs/tmp', ['__pycache__/']) == c['test']
    assert BackupConfigEntry('another_test', None, '/home', '/mnt/backups/homes', ['dummy', 'foo', '.cache']) == c['another_test']
    