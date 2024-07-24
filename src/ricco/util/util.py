import builtins
import datetime
import json
import logging
import re
import uuid
import warnings
from ast import literal_eval
from itertools import chain
from itertools import groupby

import numpy as np
import pandas as pd

from ..base import ensure_list
from ..base import is_empty
from ..base import not_empty
from .decorator import check_null
from .decorator import check_str


def to_json_string(string, errors='raise'):
  """将字符串转为json格式的字符串"""
  assert errors in ('raise', 'coerce', 'ignore'), '参数错误'
  if not isinstance(string, (list, dict)):
    try:
      string = literal_eval(string)
    except ValueError as e:
      if errors == 'raise':
        raise ValueError(e)
      if errors == 'coerce':
        return
      if errors == 'ignore':
        return string

  return json.dumps(string, ensure_ascii=False)


@check_str
def relstrip(string, kwd):
  """通过正则表达式删除左侧字符串"""
  return re.sub(f'^{kwd}', '', string)


@check_str
def rerstrip(string, kwd):
  """通过正则表达式删除右侧字符串"""
  return re.sub(f'{kwd}$', '', string)


def get_shortest_element(elements: list):
  """获取列表中长度最短的元素"""

  @check_null(default_rv=np.inf)
  def condition(string):
    string = str(string)
    return len(string)

  return min(elements, key=condition)


def and_(*conditions):
  """对多个条件执行and操作"""
  assert len(conditions) >= 1, '最少一个条件'
  res = conditions[0]
  for c in conditions[1:]:
    res = res & c
  return res


def or_(*conditions):
  """对多个条件执行or操作"""
  cond = []
  for c in conditions:
    if isinstance(c, (list, tuple)):
      cond.extend(list(c))
    else:
      cond.append(c)
  assert len(cond) >= 1, '最少一个条件'
  res = cond[0]
  for c in cond[1:]:
    res = res | c
  return res


def physical_age(birthday: datetime.datetime,
                 deadline: datetime.datetime = None):
  """计算周岁，默认按照当前时间点计算"""
  now = deadline or datetime.datetime.now()
  now_str = now.strftime('%m%d')
  birth_str = birthday.strftime('%m%d')
  if now_str >= birth_str:
    return now.year - birthday.year
  else:
    return now.year - birthday.year - 1


def first_notnull_value(series):
  """筛选第一个不为空的值"""
  for v in series:
    if not_empty(v):
      return v
  warnings.warn('所有值均为空值')


@check_null()
def pinyin(word: str) -> str:
  """将中文转换为汉语拼音"""
  import pypinyin
  assert isinstance(word, str), '输入参数必须为字符串'
  s = ''
  for i in pypinyin.pinyin(word, style=pypinyin.NORMAL):
    s += ''.join(i)
  return s


@check_null(default_rv=False)
def is_valid_uuid(uuid_to_test, version=4):
  """判断一个字符是否是uuid"""
  try:
    uuid_obj = uuid.UUID(uuid_to_test, version=version)
  except ValueError:
    return False
  return str(uuid_obj) == uuid_to_test


@check_null(default_rv=uuid.uuid4())
def get_uuid(s):
  """针对格式错误的uuid和空白值生成新的uuid"""
  if is_valid_uuid(s):
    return s
  return uuid.uuid4()


@check_null(default_rv=np.nan)
def per2float(string: str) -> float:
  """带有百分号的数值字符串转小数点形式的数值，没有百分号的返回原值"""
  if string.endswith('%'):
    string = string.rstrip('%')
    return float(string) / 100
  return float(string)


@check_null()
def extract_num(string: str,
                num_type: str = 'str',
                method: str = 'list',
                join_list: bool = False,  # noqa
                ignore_pct: bool = True,
                multi_warning=False):
  """
  提取字符串中的数值，默认返回所有数字组成的列表

  Args:
    string: 输入的字符串
    num_type:  输出的数字类型，int/float/str，默认为str
    method: 结果计算方法，对结果列表求最大/最小/平均/和等，numpy方法，默认返回列表本身
    join_list: 是否合并列表，默认FALSE
    ignore_pct: 是否忽略百分号，默认True
    multi_warning: 当有多个值的时候是否输出警告信息
  """
  assert num_type in ('float', 'int', 'str')
  string = str(string)
  ls = re.findall(r'\d+\.?\d*' if ignore_pct else r'\d+\.?\d*%?', string)
  if not ls:
    return
  if method == 'list':
    return ls if num_type == 'str' else [
      getattr(builtins, num_type)(per2float(i)) for i in ls
    ]
  if multi_warning and len(ls) >= 2:
    warnings.warn(f'有多个值进行了"{method}"运算')
  ls = [float(per2float(i)) for i in ls]
  return getattr(np, method)(ls)


@check_null()
def to_float(string,
             rex_method: str = 'mean',
             ignore_pct: bool = False,
             multi_warning=True):
  """字符串转换为float"""
  return extract_num(string,
                     num_type='float',
                     method=rex_method,
                     ignore_pct=ignore_pct,
                     multi_warning=multi_warning)


@check_null()
def house_type_format(x):
  """
  通过正则表达式将户型统一修改为1房，2房···5房及以上，目前只支持9室以下户型，
  其中5室及以上的类别为“5房及以上”
  """
  from ..resource import UTIL_CN_NUM
  if re.match('^[1-4][室房]$', x) or x == '5房及以上':
    return x
  exp = ''.join(UTIL_CN_NUM.keys())
  if res_num := re_fast(fr'([{exp}\d+])[室房]', str(x)):
    for ori, dst in UTIL_CN_NUM.items():
      res_num = res_num.replace(ori, dst)
    if int(res_num) <= 4:
      return f'{res_num}房'
    else:
      return '5房及以上'


@check_null()
def segment(x: (int, float),
            gap: (list, tuple, set, float, int),
            sep: str = '-',
            unit: str = '',
            bottom: str = '以下',
            top: str = '以上') -> str:
  """
  区间段划分工具

  Args:
    x: 数值
    gap: 间隔，固定间隔或列表
    unit: 单位，末尾
    sep: 分隔符，中间
    bottom: 默认为“以下”：80米以下
    top: 默认为“以上”：100米以上
  Returns: 区间段 'num1分隔符num2单位'：‘80-100米’
  """

  def between_list(_x, lis):
    for i in reversed(range(len(lis) - 1)):
      if _x >= lis[i]:
        return lis[i], lis[i + 1]

  assert isinstance(gap, (list, tuple, set, int, float))

  x = to_float(x)
  if isinstance(gap, (list, tuple, set)):
    gap = sorted(list(set(gap)))
    if x < gap[0]:
      return f'{gap[0]}{unit}{bottom}'
    if x >= gap[-1]:
      return f'{gap[-1]}{unit}{top}'
    return f'{between_list(x, gap)[0]}{sep}{between_list(x, gap)[1]}{unit}'

  if isinstance(gap, (int, float)):
    if x >= 0:
      return f'{int(x / gap) * gap}{sep}{int(x / gap) * gap + gap}{unit}'
    else:
      return f'{int(x / gap) * gap - gap}{sep}{int(x / gap) * gap}{unit}'


def to_str_list(series: (list, pd.Series, tuple)) -> list:
  """将列表中的元素保留为字符串、唯一、非空"""
  return list(set([str(i) for i in series if not_empty(i)]))


@check_null(default_rv=(None, None, None, None))
def fuzz_match(string: str,
               string_set: (list, pd.Series, tuple),
               fix_string_set: bool = False,
               valid_score: int = 0):
  """
  为某一字符串从某一集合中匹配相似度最高的元素

  Args:
    string: 输入的字符串
    string_set: 要去匹配的集合
    fix_string_set: 是否修复string_set中的异常数据，使用该选项会降低性能
    valid_score: 相似度大于该值的才返回
  Returns: 字符串及相似度组成的列表
  """
  from fuzzywuzzy import fuzz
  w = 0.3

  def score(x, s):
    return fuzz.partial_ratio(x, s) + fuzz.ratio(x, s) * w

  if fix_string_set:
    string_set = to_str_list(string_set)
  if is_empty(string_set):
    return None, None, None, None
  if string in string_set:
    return string, 100, 100, 100.0
  max_s = max(string_set, key=lambda x: score(x, string))

  ratio = fuzz.ratio(string, max_s)
  p_ratio = fuzz.partial_ratio(string, max_s)
  if ratio < valid_score and p_ratio < valid_score:
    return None, None, None, None
  return max_s, ratio, p_ratio, round((ratio * w + p_ratio) / (1 + w), 2)


def get_city_id_by_name(city: str):
  """获取城市代码"""
  from ..resource.city_id import CITY_IDS
  city_id = CITY_IDS.get(city if city.endswith('市') else f'{city}市')
  if not city_id:
    logging.warning('获取city_id失败，请补充该城市')
  return city_id


def sort_by_list(src_list, by_list, filter_=False) -> list:
  """
  根据一个列表对另一个列表进行筛选或排序，参照列表中不存在的元素按照原始顺序排列在后

  Args:
    src_list: 要进行排序的列表
    by_list: 参照的列表
    filter_: 是否根据参照列表筛选

  Examples:
    >>> a = [1, 2, 3, 4, 5]
    >>> b = [2, 5, 4, 1]
    >>> sort_by_list(a, b)
    [2, 5, 4, 1, 3]
    >>> sort_by_list(a, b, filter_=True)
    [2, 5, 4, 1]
    >>> sort_by_list(b, a)
    [1, 2, 4, 5]
  """
  res = [i for i in by_list if i in src_list]
  if not filter_:
    _res = [i for i in src_list if i not in res]
    res.extend(_res)
  return res


def remove_null_in_dict(dic: dict) -> dict:
  """将字典中值为空的元素删掉"""
  return {
    k: v
    for k, v in dic.items()
    if not_empty(v)
  }


def union_str_v2(*strings, sep='') -> str:
  """
  连接字符串，空白字符串会被忽略

  Args:
    *strings: 要连接字符串，依次传入
    sep: 连接符，默认为空白字符串

  Examples:
    >>> union_str_v2('a', 'b', sep='-')
    'a-b'
    >>> union_str_v2('a', 'b', 'c')
    'abc'

  """
  if strings := [i for i in strings if not_empty(i) and i != '']:
    return sep.join(strings)


def union_list_v2(*lists) -> list:
  """
  合并列表

  Examples:
    >>> a = [1]
    >>> b = [2, 3]
    >>> union_list_v2(a, b)
    [1, 2, 3]
  """
  lists = [ensure_list(i) for i in lists if not_empty(i)]
  return list(chain(*lists))


@check_null()
def eval_(x: str):
  """将文本型的列表、字典等转为真正的类型"""
  return literal_eval(x)


@check_null(default_rv={})
def list2dict(x: list):
  """列表转为字典，key为元素的顺序"""
  return {i: j for i, j in enumerate(x)}


def re_fast(pattern, string, warning=True):
  """根据正则表达式快速提取匹配到的第一个"""
  if isinstance(string, str):
    if ls := re.findall(pattern, string):
      if warning and len(ls) >= 2:
        warnings.warn('匹配到多个值，默认返回第一个')
      return ls[0]


@check_null()
def rstrip_d0(x):
  """删除末尾的‘.0’,并转为str格式，适用于对手机号等场景，如：'130.0' -> '130'"""
  _x = str(x)
  if re.match(r'^\d+\.0$', _x):
    return _x[:-2]
  return x


@check_null()
def fix_str(x: str) -> (str, None):
  """将字符串两端的空格及换行符删除，如果为空白字符串则返回空值"""
  if isinstance(x, str):
    x = x.strip()
    if x == '':
      return
  return x


def interchange_dict(dic: dict) -> dict:
  """将字典的key和value互换"""
  return dict((v, k) for k, v in dic.items())


def to_bool(x,
            na=False,
            other=False,
            t_list: list = None,
            f_list: list = None):
  """
  将常见的布尔类型的代替值转为布尔类型

  Args:
    x: 输入值
    na: 空值返回真还是假
    other: 无法判断的值如何处理
      - 'raise'：抛出异常
      - 'coerce'：返回传入的值
      - 除 'raise' 和 'coerce' 之外的其他值：直接返回该值
    t_list:指定为True的类别
    f_list:指定为False的类别
  """
  if not t_list:
    t_list = ['是', 1, 1.0, '1', '1.0', 't', 'true']
  if not f_list:
    f_list = ['否', 0, '0', 'f', 'false']

  if is_empty(x):
    return na
  if isinstance(x, bool):
    return x

  x2 = x.lower() if isinstance(x, str) else x
  if x2 in t_list:
    return True
  if x2 in f_list:
    return False
  if other == 'raise':
    raise ValueError(f'无法转换的值：{x}')
  if other == 'coerce':
    return x
  return other


def is_unique_series(df: pd.DataFrame,
                     key_cols: (str, list) = None,
                     ignore_na=False):
  """判断Dataframe中的某一列或某几列的组合是否唯一"""
  df = df.copy()
  if not key_cols:
    key_cols = df.columns.tolist()
  key_cols = ensure_list(key_cols)
  if ignore_na:
    df = df[and_(*[df[c].notna() for c in key_cols])]
  return not df.duplicated(subset=key_cols, keep=False).any()


@check_null(default_rv=False)
def is_digit(x) -> bool:
  """判断一个值是否能通过float方法转为数值型"""
  if isinstance(x, (float, int)):
    return True
  if isinstance(x, str):
    if re.match(r'\d+\.?\d*', x):
      return True
  return False


@check_null(default_rv=False)
def is_hex(string) -> bool:
  """判断一个字符串是否是十六进制格式"""
  if re.match('^[0-9a-fA-F]+$', str(string)):
    return True
  return False


def isinstance_in_list(values: list, types: (str, list)) -> bool:
  """
  检查列表内的元素类型是否全部满足多个类型之一

  Args:
    values: 要检查的值
    types: 类型类别
  """
  values = ensure_list(values)
  return all([isinstance(v, types) for v in values])


def drop_repeat_element(x: (list, tuple)):
  """
  删除列表中连续重复的元素

  Examples:
    >>> drop_repeat_element([1, 2, 2, 3, 4, 4, 4, 3])
    [1, 2, 3, 4, 3]
  """
  return [key for key, _ in groupby(x)]


def diff(ls1: list, ls2: list):
  """求两个列表的差集"""
  return list(set(ls1) - set(ls2)), list(set(ls2) - set(ls1))


def fuzz_pair(ls1, ls2, score=50):
  """模糊配对"""
  mark = 0 if len(ls1) <= len(ls2) else 1
  ls_iter = ls1 if mark == 0 else ls2
  ls_set = ls1 if mark != 0 else ls2

  res_list = []
  for i in ls_iter:
    rv = fuzz_match(i, ls_set)
    if rv[3] is not None and rv[3] > score:
      res_list.append([i, rv[0]] if mark == 0 else [rv[0], i])
  return res_list


def check_diff(ls1: list, ls2: list):
  """检查两个列表的差集"""
  res1, res2 = diff(ls1, ls2)
  print(f'左侧特有元素：{res1}')
  print(f'\n右侧特有元素：{res2}')
  print(f'\n模糊配对结果：{fuzz_pair(res1, res2)}')
