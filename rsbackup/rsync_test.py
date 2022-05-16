from rsbackup.rsync import RSync

def test_cmd():
    r = RSync('/home/alex', '.', link_dest='../2022-01-01', excludes=['.cache', '.local'], binary='rsync')
    assert r.command == ['rsync', '-a', '-v', '--delete', '/home/alex', '--link-dest', '../2022-01-01', "--exclude=.cache", "--exclude=.local", '.']

def test_cmd_no_link_dest_no_excludes():
    r = RSync('/home/alex', '.', binary='rsync')
    assert r.command == ['rsync', '-a', '-v', '--delete', '/home/alex', '.']