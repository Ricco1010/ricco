from ricco.util.os import extension
from ricco.util.os import path_name


def test_path_name():
  assert path_name('test_util.py') == 'test_util'


def test_extension():
  assert extension('test_util.py') == '.py'
