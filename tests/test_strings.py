from ricco.util.strings import drop_repeat_string
from ricco.util.strings import get_breaks
from ricco.util.strings import get_single_list


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
