from ricco.util.strings import cyclic_slice
from ricco.util.strings import drop_repeat_string
from ricco.util.strings import easy_split
from ricco.util.strings import get_breaks
from ricco.util.strings import get_single_list
from ricco.util.strings import has_chinese
from ricco.util.strings import is_repeated
from ricco.util.strings import is_seq
from ricco.util.strings import join_unique
from ricco.util.strings import punctuation_en2cn
from ricco.util.strings import remove_control_chars


def test_drop_repeat_string():
  assert drop_repeat_string(
      '112341234'
  ) == '11234'
  assert drop_repeat_string(
      '11'
  ) == '11'
  assert drop_repeat_string(
      '123123123123'
  ) == '123'
  assert drop_repeat_string(
      '上海市/普陀区/甘泉路街道/志丹路志丹路490号/志丹路志丹路490号'
  ) == '上海市/普陀区/甘泉路街道/志丹路490号'


def test_get_single_list():
  assert get_single_list(0, 7, 3) == [[0, 3], [3, 6], [6, 7]]


def test_get_breaks():
  assert get_breaks(10, 3) == [
    [[0, 3], [3, 6], [6, 9], [9, 10]],
    [[0, 1], [1, 4], [4, 7], [7, 10]],
    [[0, 2], [2, 5], [5, 8], [8, 10]]
  ]


def test_is_repeated():
  assert is_repeated('1111') is True
  assert is_repeated('1111', min_length=3) is False
  assert is_repeated('12121212') is True
  assert is_repeated('1212121') is False
  assert is_repeated('123123') is True
  assert is_repeated('123123', min_length=4) is False


def test_easy_split():
  assert easy_split('a,b;c') == ['a', 'b', 'c']
  assert easy_split('a，b、c') == ['a', 'b', 'c']
  assert easy_split('hello', seps=['x']) == ['hello']
  assert easy_split(None) == []


def test_punctuation_en2cn():
  assert punctuation_en2cn('Hello,world!') == 'Hello，world！'
  assert punctuation_en2cn('a.b?c') == 'a。b？c'
  assert punctuation_en2cn('') is None
  assert punctuation_en2cn(None) is None


def test_cyclic_slice():
  assert list(cyclic_slice('abcde', 3)) == ['abc', 'bcd', 'cde']
  assert list(cyclic_slice('ab', 3)) == []
  assert list(cyclic_slice('abc', 3)) == ['abc']


def test_is_seq():
  assert is_seq('1234', 3) is True
  assert is_seq('4321', 3) is True
  assert is_seq('1357', 2) is False
  assert is_seq('12', 3) is False


def test_remove_control_chars():
  assert remove_control_chars('hello\x00world') == 'hello world'
  assert remove_control_chars('a "quoted" string') == 'a quoted string'
  assert remove_control_chars('  spaces  ') == 'spaces'


def test_has_chinese():
  assert has_chinese('你好') is True
  assert has_chinese('hello') is False
  assert has_chinese('hello你好') is True


def test_join_unique():
  assert join_unique(['a', 'a', 'b', 'b', 'c']) == 'abc'
  assert join_unique([]) == ''
