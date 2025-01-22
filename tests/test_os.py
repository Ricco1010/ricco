from ricco.util.os import ensure_dir
from ricco.util.os import extension
from ricco.util.os import path_name
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
