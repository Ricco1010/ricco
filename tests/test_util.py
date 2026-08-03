import re
from datetime import datetime

import numpy as np
import pandas as pd

from ricco.util.util import and_
from ricco.util.util import diff
from ricco.util.util import drop_repeat
from ricco.util.util import eval_
from ricco.util.util import extract_num
from ricco.util.util import first_notnull_value
from ricco.util.util import fix2str
from ricco.util.util import fix_str
from ricco.util.util import fuzz_match
from ricco.util.util import get_shortest_element
from ricco.util.util import get_uuid
from ricco.util.util import house_type_format
from ricco.util.util import interchange_dict
from ricco.util.util import is_digit
from ricco.util.util import is_hex
from ricco.util.util import is_valid_uuid
from ricco.util.util import isinstances
from ricco.util.util import list2dict
from ricco.util.util import or_
from ricco.util.util import per2float
from ricco.util.util import physical_age
from ricco.util.util import pinyin
from ricco.util.util import re_fast
from ricco.util.util import re_multi
from ricco.util.util import relstrip
from ricco.util.util import remove_null_in_dict
from ricco.util.util import rerstrip
from ricco.util.util import rstrip_d0
from ricco.util.util import segment
from ricco.util.util import sort_by_list
from ricco.util.util import to_bool
from ricco.util.util import to_float
from ricco.util.util import to_json_string
from ricco.util.util import to_str_list
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
  assert drop_repeat([1, 2, 2, 2, 3, 4, 3]) == [1, 2, 3, 4, 3]


def test_isinstance_in_list():
  assert isinstances([1, 2, 3], int) is True
  assert isinstances([1, 2, '3'], int) is False
  assert isinstances([1, 2, 3], (int, str)) is True


def test_to_json_string():
  assert to_json_string('[1, 2, 3]') == '[1, 2, 3]'
  assert '"a"' in to_json_string("{'a': 1}")
  assert to_json_string([1, 2]) == '[1, 2]'
  result = to_json_string({'a': 1})
  assert '"a"' in result


def test_and_or():
  df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
  assert and_(df['a'] > 1, df['b'] > 4).tolist() == [False, True, True]
  assert or_(df['a'] > 1, df['b'] > 4).tolist() == [False, True, True]


def test_physical_age():
  bday = datetime(1990, 6, 15)
  assert physical_age(bday, datetime(2020, 6, 14)) == 29
  assert physical_age(bday, datetime(2020, 6, 15)) == 30
  assert physical_age(bday, datetime(2020, 7, 1)) == 30


def test_first_notnull_value():
  assert first_notnull_value([None, None, 'a', 'b']) == 'a'
  assert first_notnull_value([0, 1, 2]) == 0


def test_is_valid_uuid():
  valid = '550e8400-e29b-41d4-a716-446655440000'
  assert is_valid_uuid(valid) is True
  assert is_valid_uuid('not-a-uuid') is False
  assert is_valid_uuid(None) is False
  assert is_valid_uuid('') is False


def test_get_uuid():
  valid = '550e8400-e29b-41d4-a716-446655440000'
  assert get_uuid(valid) == valid
  result = get_uuid('bad')
  assert is_valid_uuid(str(result)) is True
  assert get_uuid(None) is not None


def test_per2float():
  assert per2float('50%') == 0.5
  assert per2float('100%') == 1.0
  assert per2float('3.14') == 3.14
  assert per2float(None) is np.nan


def test_to_str_list():
  result = to_str_list([1, 2, 2, 3, None])
  assert set(result) == {'1', '2', '3'}
  assert to_str_list([]) == []


def test_fuzz_match():
  result = fuzz_match('上海', ['上海市', '北京', '广州市'])
  assert result[0] == '上海市'
  assert result[1] >= 80


def test_re_fast():
  assert re_fast(r'\d+', 'abc123def') == '123'
  assert re_fast(r'(\d+)', 'abc123def') == '123'
  assert re_fast(r'\d+', 'no digits') is None


def test_re_multi():
  p1 = re.compile(r'\d+')
  p2 = re.compile(r'[a-z]+')
  result = re_multi([p1, p2], 'abc123def456')
  assert '123' in result
  assert '456' in result


def test_fix2str():
  assert fix2str('  hello  ') == 'hello'
  assert fix2str('hello\n\nworld') == 'hello world'
  assert fix2str('a\tb') == 'a b'
  assert fix2str(None) == ''
  assert fix2str(123) == '123'


def test_is_hex():
  assert is_hex('abc123') is True
  assert is_hex('ABC123') is True
  assert is_hex('xyz') is False
  assert is_hex(None) is False
  assert is_hex('') is False


def test_diff():
  a, b = diff([1, 2, 3], [3, 4, 5])
  assert set(a) == {1, 2}
  assert set(b) == {4, 5}
  assert diff([], [1]) == ([], [1])
