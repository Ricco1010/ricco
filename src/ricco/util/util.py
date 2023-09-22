import builtins
import datetime
import json
import logging
import random
import re
import uuid
import warnings
from ast import literal_eval

import numpy as np
import pandas as pd
from shapely.geometry.base import BaseGeometry


def ensure_list(val):
  """将标量值和Collection类型都统一转换为LIST类型"""
  if val is None:
    return []
  if isinstance(val, list):
    return val
  if isinstance(val, (set, tuple)):
    return list(val)
  return [val]


def to_json_string(string, errors='raise'):
  """将字符串转为接送格式的字符串"""
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

  return json.dumps(string)


def relstrip(string, kwd):
  """通过正则变大是删除左侧字符串"""
  return re.sub(f'^{kwd}', '', string)


def rerstrip(string, kwd):
  """通过正则变大是删除右侧字符串"""
  return re.sub(f'{kwd}$', '', string)


def get_shortest_element(elements: list):
  """获取列表中长度最短的元素"""

  def condition(string):
    if is_empty(string):
      return np.inf
    string = str(string)
    return len(string)

  return min(elements, key=condition)


def and_(*conditions):
  if len(conditions) < 1:
    raise Exception('最少一个条件')
  res = conditions[0]
  for c in conditions[1:]:
    res = res & c
  return res


def or_(*conditions):
  cond = []
  for c in conditions:
    if isinstance(c, (list, tuple)):
      cond.extend(list(c))
    else:
      cond.append(c)
  if len(cond) < 1:
    raise Exception('最少一个条件')
  res = cond[0]
  for c in cond[1:]:
    res = res | c
  return res


def physical_age(birthday: datetime.datetime,
                 deadline: datetime.datetime = None):
  """计算周岁，默认按照当前时间点计算"""
  now = deadline if deadline else datetime.datetime.now()
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


def pinyin(word: str) -> str:
  """将中文转换为汉语拼音"""
  import pypinyin
  if isinstance(word, str):
    s = ''
    for i in pypinyin.pinyin(word, style=pypinyin.NORMAL):
      s += ''.join(i)
  else:
    raise TypeError('输入参数必须为字符串')
  return s


def is_valid_uuid(uuid_to_test, version=4):
  """判断一个字符是否是uuid"""
  try:
    uuid_obj = uuid.UUID(uuid_to_test, version=version)
  except ValueError:
    return False
  return str(uuid_obj) == uuid_to_test


def get_uuid(s):
  """针对格式错误的uuid和空白值生成新的uuid"""
  if is_empty(s) or not is_valid_uuid(s):
    return uuid.uuid4()
  return s


def per2float(string: str) -> float:
  """带有百分号的数值字符串转小数点形式的数值，没有百分号的返回原值"""
  if '%' in string:
    string = string.rstrip('%')
    return float(string) / 100
  return float(string)


def extract_num(string: str,
                num_type: str = 'str',
                method: str = 'list',
                join_list: bool = False,
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
  string = str(string)
  if ignore_pct:
    lis = re.findall(r"\d+\.?\d*", string)
  else:
    lis = re.findall(r"\d+\.?\d*%?", string)
  lis2 = [getattr(builtins, num_type)(per2float(i)) for i in lis]
  if len(lis2) > 0:
    if method != 'list':
      if join_list:
        raise ValueError(
            "计算结果无法join，只有在method='list'的情况下, 才能使用join_list=True")
      if multi_warning & (len(lis2) >= 2):
        warnings.warn(f'有多个值进行了{method}运算')
      res = getattr(np, method)(lis2)
    else:
      if num_type == 'str':
        res = ['{:g}'.format(float(j)) for j in lis2]
      else:
        res = lis2
      if join_list:
        res = ''.join(res)
  else:
    res = None
  return res


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


def house_type_format(x):
  """
  通过正则表达式将户型统一修改为1房，2房···5房及以上，目前只支持9室以下户型，
  其中5室及以上的类别为“5房及以上”
  """
  from ..resource import UTIL_CN_NUM
  if is_empty(x):
    return
  if re.match('^[1-4][室房]$', x) or x == '5房及以上':
    return x
  exp = ''.join(UTIL_CN_NUM.keys())
  if res_num := re_fast(f'([{exp}\d])[室房]', str(x)):
    for ori, dst in UTIL_CN_NUM.items():
      res_num = res_num.replace(ori, dst)
    if int(res_num) <= 4:
      return f'{res_num}房'
    else:
      return '5房及以上'


def segment(x,
            gap: (list, float, int),
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

  x = to_float(x)
  if x is None:
    return ''
  elif isinstance(gap, list):
    gap = sorted(list(set(gap)))
    if x < gap[0]:
      return f'{gap[0]}{unit}{bottom}'
    elif x >= gap[-1]:
      return f'{gap[-1]}{unit}{top}'
    else:
      return f'{between_list(x, gap)[0]}{sep}{between_list(x, gap)[1]}{unit}'
  elif isinstance(gap, (int, float)):
    if x >= 0:
      return f'{int(x / gap) * gap}{sep}{int(x / gap) * gap + gap}{unit}'
    else:
      return f'{int(x / gap) * gap - gap}{sep}{int(x / gap) * gap}{unit}'
  else:
    raise TypeError('gap参数数据类型错误')


def fuzz_match(string: str, string_set: (list, pd.Series, tuple)):
  """
  为某一字符串从某一集合中匹配相似度最高的元素
  Args:
    string: 输入的字符串
    string_set: 要去匹配的集合
  Returns: 字符串及相似度组成的列表
  """
  from fuzzywuzzy import fuzz
  string_set = [str(i) for i in string_set if not_empty(i)]
  if is_empty(string) or is_empty(string_set):
    return None, None, None
  if string in string_set:
    return string, 100, 100
  max_s = max(string_set, key=lambda x: fuzz.ratio(x, string))
  return max_s, fuzz.ratio(string, max_s), fuzz.partial_ratio(string, max_s)


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


def is_empty(x) -> bool:
  """
  判断是否为空值，以下值认为是空白
    - 空白列表、字典, 如：[], {}，
    - 空白Dataframe、series, 如：pd.DataFrame()
    - 空白shapely格式的geometry，如：Point(np.nan, np.nan)
  """
  if isinstance(x, (list, dict, tuple)):
    return False if x else True
  if isinstance(x, (pd.DataFrame, pd.Series)):
    return x.empty
  if isinstance(x, BaseGeometry):
    return x.is_empty
  return pd.isna(x)


def not_empty(x) -> bool:
  """判断是否非空"""
  return not is_empty(x)


def union_str(strings: list, sep='') -> (str, None):
  """连接字符串"""
  warnings.warn('方法即将停用，请使用union_str_v2', DeprecationWarning)
  if is_empty(strings):
    return
  if strings := [i for i in strings if not_empty(i)]:
    return sep.join(strings)


def union_str_v2(*strings, sep='') -> str:
  """
  连接字符串，空白字符串会被忽略
  Examples:
    >>> union_str_v2('a', 'b', sep='-') # 'a-b'
    >>> union_str_v2('a', 'b', 'c') # 'abc'
  """
  if strings := [i for i in strings if not_empty(i) and i != '']:
    return sep.join(strings)


def union_list(s) -> list:
  """合并列表"""
  warnings.warn('方法即将停用，请使用union_list_v2', DeprecationWarning)
  if is_empty(s):
    return []
  lis = s[0]
  for i in s[1:]:
    lis.extend(i)
  return lis


def union_list_v2(*lists) -> list:
  """合并列表"""
  res = ensure_list(lists[0])
  for i in lists[1:]:
    res.extend(ensure_list(i))
  return res


def eval_(x: str):
  """将文本型的列表、字典等转为真正的类型"""
  return literal_eval(x) if not_empty(x) else None


def list2dict(x: list):
  """列表转为字典，key为元素的顺序"""
  if is_empty(x):
    return {}
  return {i: j for i, j in enumerate(x)}


def re_fast(pattern, string, warning=True):
  """根据正则表达式快速提取匹配到的第一个"""
  if isinstance(string, str):
    if ls := re.findall(pattern, string):
      if warning and len(ls) >= 2:
        warnings.warn('匹配到多个值，默认返回第一个')
      return ls[0]


def random_name():
  """随机生成中文名字，仅生成2或3字名字"""
  from ..resource.names import FirstName
  from ..resource.names import LastName
  c = [random.choice(FirstName)]
  for i in range(random.randint(1, 2)):
    c.append(random.choice(LastName))
  return ''.join(c)


def random_date():
  """获取随机日期"""
  now = datetime.datetime.now()
  tsp = int(datetime.datetime.timestamp(now))
  tsp = random.randrange(-946800000, tsp)
  return datetime.datetime.fromtimestamp(tsp).strftime("%Y%m%d")


def random_room_number(unit=False):
  """生成随机的房间号"""
  floor = random.randint(1, 17)
  room = random.randint(1, 4)
  room = str(room).zfill(2)
  if unit:
    _u = random.randint(1, 6)
    _unit = f'{_u}单元'
    return f'{_unit}{floor}{room}'
  return f'{floor}{room}'


def random_by_prob(mapping: dict):
  """根据概率生成随机值"""
  return np.random.choice(
      list(mapping.keys()),
      p=np.array(list(mapping.values())).ravel()
  )


def to_int_str(x):
  """将由数字转成的字符串转为int格式的，针对手机号等场景，如：'130.0' -> '130'"""
  warnings.warn('即将弃用，请使用 rstrip_d0', DeprecationWarning)
  return rstrip_d0(x)


def rstrip_d0(x):
  """删除末尾的‘.0’,并转为str格式，适用于对手机号等场景，如：'130.0' -> '130'"""
  if is_empty(x):
    return
  _x = str(x)
  if re.match('^\d+\.0$', _x):
    return _x[:-2]
  return x


def fix_empty_str(x: str) -> (str, None):
  """将字符串两端的空格及换行符删除，如果为空白字符串则返回空值"""
  warnings.warn('即将弃用，请使用fix_str', DeprecationWarning)
  return fix_str(x)


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
            na: bool = False,
            other: (bool, str) = False,
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
      - 除'raise'和'coerce'之外的其他值：直接返回该值
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
  """判断是否唯一"""
  df = df.copy()
  if not key_cols:
    key_cols = df.columns.tolist()
  key_cols = ensure_list(key_cols)
  if ignore_na:
    df = df[and_(*[df[c].notna() for c in key_cols])]
  return not df.duplicated(subset=key_cols, keep=False).any()


def is_digit(x) -> bool:
  """判断一个值是否能通过float方法转为数值型"""
  if is_empty(x):
    return False
  if isinstance(x, (float, int)):
    return True
  if isinstance(x, str):
    if re.match(r'\d+\.?\d*', x):
      return True
  return False


def is_hex(string) -> bool:
  """判断一个字符串是否是十六进制"""
  if is_empty(string):
    return False
  if re.match('^[0-9a-fA-F]+$', str(string)):
    return True
  return False
