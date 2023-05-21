
import io
import os
import shutil
import tempfile
import sys

from rsbackup import RSync

from rsbackup import __version__
from rsbackup.__main__ import main


def test_acceptance_list():
    with AcceptanceTestFixture() as fixture:
        out = fixture.run('list')

        assert out == f"""rsbackup v{__version__}
https://github.com/halimath/rsbackup

test
  Sources:
    - {os.path.join(fixture.dir_name, 'src')}
  Target:
    {os.path.join(fixture.dir_name, 'bak')}
  Excludes:
    - foo

"""


def test_acceptance_create_single_source():
    with AcceptanceTestFixture() as fixture:
        fixture.create_src_file('spam', 'Spam and eggs')
        print(fixture.run('create', 'test'))
        assert 'Spam and eggs' == fixture.read_backup_file('_latest', 'src',
                                                           'spam')


def test_acceptance_create_multiple_sources_with_excluded_source():
    with AcceptanceTestFixture() as fixture:
        fixture.create_src_file('spam', 'Spam and eggs')
        fixture.create_src_file('foo', 'Foo and bar')
        fixture.sources = [os.path.join(
            'src', 'spam'), os.path.join('src', 'foo')]
        fixture.write_config_file()

        print(fixture.run('create', 'test'))
        assert 'Spam and eggs' == fixture.read_backup_file('_latest', 'spam')
        assert not fixture.backup_file_exists('_latest', 'foo')


def test_acceptance_create_multiple_sources():
    with AcceptanceTestFixture() as fixture:
        fixture.create_src_file('spam', 'Spam and eggs')
        fixture.create_src_file('foobar', 'Foo and bar')
        fixture.sources = [os.path.join(
            'src', 'spam'), os.path.join('src', 'foobar')]
        fixture.write_config_file()

        print(fixture.run('create', 'test'))
        assert 'Spam and eggs' == fixture.read_backup_file(
            '_latest', 'spam')
        assert 'Foo and bar' == fixture.read_backup_file(
            '_latest', 'foobar')


class AcceptanceTestFixture:
    def __init__(self):
        self._dir = tempfile.TemporaryDirectory(prefix='rsbackup_test_')
        self.dir_name = self._dir.name
        self.config_file = os.path.join(self.dir_name, 'rsbackup.toml')
        self.sources = ['src']

    def create_src_file(self, name, content):
        with open(os.path.join(self.dir_name, 'src', name), mode='w') as f:
            f.write(content)

    def read_backup_file(self, *path):
        with open(os.path.join(self.dir_name, 'bak', *path), mode='r') as f:
            return f.read()

    def backup_file_exists(self, *path):
        try:
            os.stat(os.path.join(self.dir_name, 'bak', *path))
            return True
        except:
            return False

    def __enter__(self):
        self.write_config_file()

        os.makedirs(os.path.join(self.dir_name, 'src'))
        os.makedirs(os.path.join(self.dir_name, 'bak'))

        return self

    def write_config_file(self):
        with open(self.config_file, mode='w') as f:
            print(f"""
[test]
sources = ['{"', '".join(os.path.join(self.dir_name, src) for src in self.sources)}']
target = '{os.path.join(self.dir_name, 'bak')}'
excludes = [
    'foo',
]
            """, file=f)

    def __exit__(self, error_type=None, value=None, traceback=None):
        if error_type:
            copy = self.dir_name + '.keep'
            print(f"Copying temporary directory to {copy}")
            shutil.copytree(self.dir_name, copy)

        self._dir.cleanup()

    def run(self, *args):
        collector = FDCollector()
        with collector:
            main(['-c', self.config_file] + [a for a in args])
        return collector.out


class FDCollector:
    def __init__(self, file='stdout'):
        self._file = file

    def __enter__(self):
        self._buffer = io.StringIO()

        self._old = getattr(sys, self._file)
        setattr(sys, self._file, self._buffer)

        return self

    def __exit__(self, error_type=None, value=None, traceback=None):
        self._buffer.seek(0)
        self.out = self._buffer.read()
        setattr(sys, self._file, self._old)


def test_cmd():
    r = RSync(('/home/alex',), '.', link_dest='../2022-01-01',
              excludes=['.cache', '.local'], binary='rsync')
    assert r.command == ['rsync', '--archive', '--verbose', '--delete', '/home/alex',
                         '--link-dest', '../2022-01-01', '--exclude=.cache',
                         '--exclude=.local', '.']


def test_cmd_no_link_dest_no_excludes():
    r = RSync(('/home/alex',), '.', binary='rsync')
    assert r.command == ['rsync', '--archive',
                         '--verbose', '--delete', '/home/alex', '.']
