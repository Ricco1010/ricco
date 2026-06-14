import os
import tempfile

from ricco.util.os import count_files
from ricco.util.os import dir_iter
from ricco.util.os import dir_iter_list
from ricco.util.os import ensure_dir
from ricco.util.os import ensure_dirpath_exist
from ricco.util.os import ext
from ricco.util.os import extension
from ricco.util.os import fn
from ricco.util.os import path_name
from ricco.util.os import single_ext
from ricco.util.os import split_path


def test_path_name():
  assert path_name('test_util.py') == 'test_util'


def test_extension():
  assert extension('test_util.py') == '.py'


def test_split_path():
  assert split_path('/path/test.txt') == ('/path', 'test', '.txt')
  assert split_path('/path/2/test.txt') == ('/path/2', 'test', '.txt')


def test_ensure_dir():
  assert ensure_dir('/path/') == '/path/'
  assert ensure_dir('/path') == '/path/'


def test_ext():
  assert ext('test.csv') == '.csv'
  assert ext('/path/to/file.txt') == '.txt'
  assert ext('no_ext') == ''


def test_fn():
  assert fn('test.csv') == 'test'
  assert fn('/path/to/file.txt') == '/path/to/file'


def test_count_files():
  with tempfile.TemporaryDirectory() as tmpdir:
    open(os.path.join(tmpdir, 'a.txt'), 'w').close()
    open(os.path.join(tmpdir, 'b.txt'), 'w').close()
    assert count_files(tmpdir) == 2


def test_single_ext():
  assert single_ext(['a.csv', 'b.csv']) == '.csv'
  assert single_ext(['a.csv', 'b.txt']) is None
  assert single_ext([]) is None


def test_dir_iter():
  with tempfile.TemporaryDirectory() as tmpdir:
    open(os.path.join(tmpdir, 'a.csv'), 'w').close()
    open(os.path.join(tmpdir, 'b.txt'), 'w').close()
    files = list(dir_iter(tmpdir))
    assert len(files) == 2
    csv_files = list(dir_iter(tmpdir, exts='.csv'))
    assert len(csv_files) == 1


def test_dir_iter_list():
  with tempfile.TemporaryDirectory() as tmpdir:
    open(os.path.join(tmpdir, 'a.csv'), 'w').close()
    open(os.path.join(tmpdir, 'b.csv'), 'w').close()
    result = dir_iter_list(tmpdir)
    assert len(result) == 2
    assert isinstance(result, list)


def test_ensure_dirpath_exist():
  with tempfile.TemporaryDirectory() as tmpdir:
    new_dir = os.path.join(tmpdir, 'sub', 'deep')
    filepath = os.path.join(new_dir, 'test.txt')
    ensure_dirpath_exist(filepath)
    assert os.path.isdir(new_dir)
