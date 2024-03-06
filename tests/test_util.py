import numpy as np

from ricco.util.util import drop_repeat_element
from ricco.util.util import eval_
from ricco.util.util import extract_num
from ricco.util.util import fix_str
from ricco.util.util import get_shortest_element
from ricco.util.util import house_type_format
from ricco.util.util import interchange_dict
from ricco.util.util import is_digit
from ricco.util.util import isinstance_in_list
from ricco.util.util import list2dict
from ricco.util.util import pinyin
from ricco.util.util import relstrip
from ricco.util.util import remove_null_in_dict
from ricco.util.util import rerstrip
from ricco.util.util import rstrip_d0
from ricco.util.util import segment
from ricco.util.util import sort_by_list
from ricco.util.util import to_bool
from ricco.util.util import to_float
from ricco.util.util import union_list_v2
from ricco.util.util import union_str_v2


def test_relstrip():
  assert relstrip('257号2234', '257号') == '2234'


def test_rerstrip():
  assert rerstrip('257号2234', '234') == '257号2'


def test_get_get_shortest_element():
  assert get_shortest_element(
      ['123', '1', '3211', 'abcdef']
  ) == '1'
  assert get_shortest_element(
      ['123', 1, '3211', 'abcdef']
  ) == 1
  assert get_shortest_element(
      [None, 'sssssss', 'sssssss', '3211', 'abcdef']
  ) == '3211'


def test_pinyin():
  assert pinyin('测试') == 'ceshi'
  assert pinyin('test') == 'test'


def test_extract_num():
  string = 'fo13--;gr35.3'
  assert extract_num(string) == ['13', '35.3']
  assert extract_num(string, num_type='int') == [13, 35]
  assert extract_num(string, num_type='float') == [13.0, 35.3]


def test_to_float():
  assert to_float('6.5') == 6.5
  assert to_float('6.5%') == 0.065
  assert to_float('6.5%', ignore_pct=True) == 6.5
  assert to_float('p6.5%') == 0.065
  assert to_float('p6.5') == 6.5
  assert to_float('p6.5xx3.5', multi_warning=False) == 5.0
  assert to_float('p6.5xx3.5', rex_method='min', multi_warning=False) == 3.5
  assert to_float('p6.5xx3.5', rex_method='max', multi_warning=False) == 6.5
  assert to_float('p6.5xx3.5', rex_method='sum', multi_warning=False) == 10.0


def test_segment():
  assert segment(55, 20) == '40-60'
  assert segment(55, 20, sep='--', unit='米') == '40--60米'
  assert segment(55, [20]) == '20以上'
  assert segment(10, [20, 50], unit='米') == '20米以下'
  assert segment(20, [20, 50], unit='米') == '20-50米'
  assert segment(50, [20, 50], unit='米') == '50米以上'


def test_house_type_format():
  assert house_type_format('一室一厅') == '1房'
  assert house_type_format('两室一厅') == '2房'
  assert house_type_format('3室两厅') == '3房'
  assert house_type_format('4房1厅') == '4房'
  assert house_type_format('5室1厅') == '5房及以上'
  assert house_type_format('8室1厅') == '5房及以上'


def test_list2dict():
  assert list2dict([1, 2, 3]) == {0: 1, 1: 2, 2: 3}


def test_eval():
  assert eval_(None) == None
  assert eval_('[1]') == [1]
  assert eval_("{'a':1}") == {'a': 1}


def test_union_str():
  assert union_str_v2('abc', 'def') == 'abcdef'
  assert union_str_v2('abc', 'def', sep='|') == 'abc|def'
  assert union_str_v2('abc', None) == 'abc'


def test_union_list():
  assert union_list_v2([1, 2, 3]) == [1, 2, 3]
  assert union_list_v2([1, 2, 3], [4, 5]) == [1, 2, 3, 4, 5]
  assert union_list_v2([1, 2, 3], 4, 5) == [1, 2, 3, 4, 5]


def test_sort_by_list():
  src_list = [1, 2, 3, 4, 5]
  by_list = [4, 5, 3, 6]
  assert sort_by_list(src_list, by_list, filter_=False) == [4, 5, 3, 1, 2]
  assert sort_by_list(src_list, by_list, filter_=True) == [4, 5, 3]


def test_fix_empty_str():
  assert fix_str(1) == 1
  assert fix_str('a') == 'a'
  assert fix_str(' a ') == 'a'
  assert fix_str('\na\n') == 'a'
  assert fix_str('') == None
  assert fix_str(' ') == None
  assert fix_str(' \n') == None
  assert fix_str(' ') == None


def test_is_digit():
  assert is_digit(1) is True
  assert is_digit('1') is True
  assert is_digit('1.1') is True
  assert is_digit('a') is False
  assert is_digit(None) is False
  assert is_digit(np.nan) is False


def test_rstrip_d0():
  assert rstrip_d0('') == ''
  assert rstrip_d0(0) == 0
  assert rstrip_d0(1.0) == '1'
  assert rstrip_d0('a') == 'a'
  assert not rstrip_d0(None)
  assert not rstrip_d0(np.nan)


def test_to_bool():
  assert to_bool(1) is True
  assert to_bool('是') is True
  assert to_bool('0') is False
  assert to_bool('否') is False
  assert to_bool(None) is False
  assert to_bool(None, na=True) is True
  assert to_bool(123) is False
  assert to_bool(123, other=True) is True
  assert to_bool(123, other='abc') == 'abc'


def test_interchange_dict():
  assert interchange_dict({1: 2}) == {2: 1}


def test_remove_null_in_dict():
  assert remove_null_in_dict({1: 2, 3: None, 4: None}) == {1: 2}


def test_drop_repeat_element():
  assert drop_repeat_element([1, 2, 2, 2, 3, 4, 3]) == [1, 2, 3, 4, 3]


def test_isinstance_in_list():
  assert isinstance_in_list([1, 2, 3], int) is True
  assert isinstance_in_list([1, 2, '3'], int) is False
  assert isinstance_in_list([1, 2, 3], (int, str)) is True
