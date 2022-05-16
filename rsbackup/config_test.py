from rsbackup.config import load, BackupConfig, BackupConfigEntry

def test_load ():
    input = """
- name: Test
  description: A backup configuration for tests
  source: ./backup
  target: ./tmp
  excludes:
  - __pycache__
- name: "Another test"
  source: /home
  target: /mnt/backups/homes
  excludes:
  - dummy
  - foo
  - .cache    
    """
    c = load(input, '/spam/eggs')
    assert 2 == len(c)
    assert BackupConfigEntry('Test', 'A backup configuration for tests', '/spam/eggs/backup', '/spam/eggs/tmp', ['__pycache__']) == c['Test']
    assert BackupConfigEntry('Another test', None, '/home', '/mnt/backups/homes', ['dummy', 'foo', '.cache']) == c['Another test']
    