import logging
import re

from ..base import ensure_list
from .decorator import check_null
from .util import drop_repeat
from .util import get_shortest_element


def extract_city(string: str, na=None):
  """从字符串中提取城市（可能包含县级市）"""
  logging.warning(
      "extract_city is deprecated, use mdt_biz_util.util.district.extract_city instead",
      DeprecationWarning
  )
  from .district import extract_city as _
  return _(string, na)


def get_single_list(start, length, step):
  """
  获取单个起点的位置端点列表，如果起始位置不是零，则会返回0到起始位置的列表
  Args:
    start: 起始位置
    length: 总长度
    step: 步长
  Examples:
    >>> get_single_list(0, 7, 3) == [[0, 3], [3, 6], [6, 7]]
    >>> get_single_list(1, 7, 3) == [[0, 1], [1, 4], [4, 7]]
  """
  if start > 0:
    res = [[0, start]]
  else:
    res = []
  for i in range(start, length, step):
    if i + step <= length:
      res.append([i, i + step])
    else:
      res.append([i, length])
  return res


def get_breaks(length, step):
  """
  通过长度和步长获所有可能的取端点列表的列表
  Examples:
    >>> get_breaks(10, 3) == [
    >>>   [[0, 3], [3, 6], [6, 9], [9, 10]],
    >>>   [[0, 1], [1, 4], [4, 7], [7, 10]],
    >>>   [[0, 2], [2, 5], [5, 8], [8, 10]]
    >>> ]
  """
  res = []
  for start in range(0, step):
    res.append(get_single_list(start, length, step))
  return res


def get_list_by_position(string: str, breaks: list):
  """
  按照位置信息将字符串拆解为多个字符串的列表
  Args:
    string: 需要拆分的字符串
    breaks: 位置集合列表的列表（左闭右开），[[1, 5], [5, 10], [10, 15]]
  """
  res = []
  for brk in breaks:
    res.append(string[brk[0]:brk[1]])
  return res


def join_unique(strs: list):
  """删除列表中连续重复的元素，并拼接成字符串"""
  strs = drop_repeat(strs)
  return ''.join(strs)


def drop_repeat_string_by_step(string, step):
  """根据指定的小块长度，获取去重后的字符串"""
  _list = []
  length = len(string)
  for breaks in get_breaks(length, step):
    res = get_list_by_position(string, breaks)
    str_drop = join_unique(res)
    _list.append(str_drop)

  return get_shortest_element(_list)


@check_null()
def drop_repeat_string(string,
                       min_length=3,
                       max_length=None):
  """
  删除连续重复的字符串，按照step从大到小删除重复字符，返回去重后最短的字符串

  Args:
    string: 要处理的字符串
    min_length: 识别的最短长度，默认为3
    max_length: 识别的最长长度，默认不限制

  Examples:
    >>> drop_repeat_string('上海市上海市杨浦区')
    '上海市杨浦区'
  """
  if len(string) < min_length * 2:
    return string
  _list = []
  if not max_length:
    max_length = len(string) // 2
  for step in range(max_length, min_length - 1, -1):
    str_drop = drop_repeat_string_by_step(string, step)
    _list.append(str_drop)
    string = get_shortest_element(_list)
  return string


@check_null(default_rv=[])
def easy_split(string: str, seps: list = None, extra_seps: list = None):
  """
  使用常见的分隔符将字符串拆分为列表

  Args:
    string:
    seps: 自定义分隔符
    extra_seps: 额外的分隔符
  """
  if '\\' in string:
    raise Exception('字符串中不能包含"\\"')
  if not seps:
    seps = [
      '，', ',',
      '、', '/',
      '；', ';',
      '。', '\\|', ' ',
    ]
  if extra_seps:
    seps.extend(extra_seps)
  seps = ensure_list(seps)
  return [i for i in re.split('|'.join(seps), string) if i]


def punctuation_en2cn(text: str):
  """将英文标点符号替换为中文标点符号"""
  if not text or text == '' or not isinstance(text, str):
    return

  replace_dict = {
    ',': '，',
    '.': '。',
    '?': '？',
    '!': '！',
    ';': '；',
    ':': '：',
    '(': '（',
    ')': '）',
    '[': '【',
    ']': '】',
    '{': '｛',
    '}': '｝',
    '"': '“',
  }
  pattern = re.compile(
      '|'.join(re.escape(key) for key in replace_dict.keys())
  )

  def _replace(match):
    return replace_dict[match.group(0)]

  return pattern.sub(_replace, text)


def cyclic_slice(s, n=5):
  """迭代生成长度为n的字符串"""
  length = len(s)
  for i in range(0, length - n + 1):
    yield s[i:i + n]


def _is_seq(_str):
  """判断一个字符串是否全部是递增或递减1的数字组成的，如‘1234’、‘876’"""
  # 初始化为递增或递减
  diff_ls = [1, -1]
  s0 = _str[0]
  for s in _str[1:]:
    _d = int(s) - int(s0)
    if _d not in diff_ls:
      return False
    # 根据前面的字符再次确定递增或递减
    diff_ls = [_d]
    s0 = s
  return True


def is_seq(num_str: str, n: int):
  """判断一个全部为数字的字符串是否含有连续n个递增或递减1的数字"""
  num_str = str(num_str)
  assert num_str.isdigit(), '输入值必须为字符串且全部由数字组成'
  length = len(num_str)
  if length < n:
    return False
  for s in cyclic_slice(num_str, n):
    if _is_seq(s):
      return True
  return False


def is_repeated(string, min_length: int = 1):
  """检查输入是重复字符串组成的字符串"""
  n = len(string)
  if min_length * 2 > n:
    return False
  for i in range(min_length, n // 2 + 1):
    if n % i == 0:
      substring = string[:i]
      if substring * (n // i) == string:
        return True
  return False
