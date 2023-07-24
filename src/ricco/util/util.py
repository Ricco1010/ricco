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

from ..resource.geometry import GeomTypeSet
from ..resource.names import FirstName
from ..resource.names import LastName
from ..resource.patterns import Pattern


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
  if not isinstance(string, (list, dict)):
    try:
      string = literal_eval(string)
    except ValueError as e:
      if errors == 'raise':
        raise ValueError(e)
      elif errors == 'coerce':
        return None
      elif errors == 'ignore':
        return string
      else:
        raise ValueError('errors传参错误')

  return json.dumps(string)


def is_ID_number(string, na=False) -> bool:
  """
  校验一个字符串是否为正确的身份证号

  :param string: 要传入的字符串
  :param na: 空值返回True还是False，默认为False
  :return:
  """
  if is_empty(string):
    return na

  if not isinstance(string, str):
    string = str(string)
  if len(string) != 18:
    return False
  if re.match(Pattern.ID_number, string):
    return True
  else:
    return False


def relstrip(string, kwd):
  return re.sub(f'^{kwd}', '', string)


def rerstrip(string, kwd):
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
    raise Exception('Must there be one condition')
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
    raise Exception('Must there be one condition')
  res = cond[0]
  for c in cond[1:]:
    res = res | c
  return res


def all_year_old(birthday: datetime.datetime,
                 deadline: datetime.datetime = None):
  now = deadline if deadline else datetime.datetime.now()
  now_str = now.strftime('%m%d')
  birth_str = birthday.strftime('%m%d')
  if now_str >= birth_str:
    return now.year - birthday.year
  else:
    return now.year - birthday.year - 1


def first_notnull_value(series):
  for v in series:
    if pd.notna(v) or not v.is_empty:
      return v
  warnings.warn('所有值均为空值')
  return None


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
  if is_empty(s):
    return uuid.uuid4()
  elif not is_valid_uuid(s):
    return uuid.uuid4()
  else:
    return s


def per2float(string: str) -> float:
  """带有百分号的数值字符串转小数点形式的数值，
  没有百分号的返回原值"""
  if '%' in string:
    string = string.rstrip('%')
    return float(string) / 100
  else:
    return float(string)


def extract_num(string: str,
                num_type: str = 'str',
                method: str = 'list',
                join_list: bool = False,
                ignore_pct: bool = True,
                multi_warning=False):
  """
  提取字符串中的数值，默认返回所有数字组成的列表

  :param string: 输入的字符串
  :param num_type:  输出的数字类型，int/float/str，默认为str
  :param method: 结果计算方法，对结果列表求最大/最小/平均/和等，numpy方法，默认返回列表本身
  :param join_list: 是否合并列表，默认FALSE
  :param ignore_pct: 是否忽略百分号，默认True
  :param multi_warning:
  :return:
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
  """
  字符串转换为float
  """
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

  exp = '|'.join(UTIL_CN_NUM.keys())
  pattern = f'([{exp}|\d])[室|房]'
  res = re.findall(pattern, str(x))
  if len(res) >= 1:
    res_num = res[0]
    for i in UTIL_CN_NUM:
      res_num = res_num.replace(i, UTIL_CN_NUM[i])
    if int(res_num) <= 4:
      return res_num + '房'
    else:
      return '5房及以上'
  else:
    return None


def segment(x,
            gap: (list, float, int),
            sep: str = '-',
            unit: str = '',
            bottom: str = '以下',
            top: str = '以上') -> str:
  """
  区间段划分工具

  :param x: 数值
  :param gap: 间隔，固定间隔或列表
  :param unit: 单位，末尾
  :param sep: 分隔符，中间
  :param bottom: 默认为“以下”：80米以下
  :param top: 默认为“以上”：100米以上
  :return: 区间段 'num1分隔符num2单位'：‘80-100米’
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


def fuzz_match(string: str, ss: (list, pd.Series)):
  """
  为某一字符串从某一集合中匹配相似度最高的元素

  :param string: 输入的字符串
  :param ss: 要去匹配的集合
  :return: 字符串及相似度组成的列表
  """
  from fuzzywuzzy import fuzz

  def _ratio(_s, x):
    return fuzz.ratio(_s, x), fuzz.partial_ratio(_s, x)

  max_r, max_pr, max_s = 0, 0, None
  for s in ss:
    r, pr = _ratio(s, string)
    if r > max_r:
      max_r = r
      max_pr = pr
      max_s = s
  return max_s, max_r, max_pr


def get_city_id_by_name(city: str):
  """获取城市代码"""
  from ..resource.city_id import CITY_IDS
  city_id = CITY_IDS.get(city if city.endswith('市') else f'{city}市')
  if not city_id:
    logging.warning('获取city_id失败，请补充该城市')
  return city_id


def sort_by_list(src_list, by_list, mode='sort') -> list:
  """
  根据一个列表对另一个列表进行筛选或排序，
  当mode为f/filter时，对列表进行筛选并排序，取二者交集；
  当mode为s/sort时，对列表进行排序，优先按照参照的列表排序，忽略没有的元素，
  参照列表中不存在的元素按照原始顺序排列在后
  Args:
    src_list: 要进行排序的列表
    by_list: 参照的列表
    mode: f/filter, s/sort
  """
  if mode not in ('f', 'filter', 's', 'sort'):
    raise ValueError('参数错误')

  res = [i for i in by_list if i in src_list]
  if mode in ('s', 'sort'):
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
  if isinstance(x, GeomTypeSet):
    return x.is_empty
  return pd.isna(x)


def not_empty(x) -> bool:
  """判断是否非空"""
  return not is_empty(x)


def union_str(lis: list, sep='') -> (str, None):
  """连接字符串"""
  if is_empty(lis):
    return None
  lis = [i for i in lis if not_empty(i)]
  if lis:
    return sep.join(lis)
  else:
    return None


def union_list(s) -> list:
  """合并列表"""
  if is_empty(s):
    return []
  lis = s[0]
  for i in s[1:]:
    lis.extend(i)
  return lis


def eval(x: str):
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
  c = [random.choice(FirstName)]
  l = random.randint(1, 2)
  for i in range(l):
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
  if is_empty(x):
    return
  try:
    return str(int(float(x)))
  except ValueError:
    return str(x)


def fix_empty_str(x: str) -> (str, None):
  """将字符串两端的空格及换行符删除，如果为空白字符串则返回空值"""
  if isinstance(x, str):
    x = x.strip()
    if x == '':
      return None
  return x


def fix_str(x: str) -> (str, None):
  """将字符串两端的空格及换行符删除，如果为空白字符串则返回空值"""
  return fix_empty_str(x)


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


def is_unique_series(df: pd.DataFrame, key_cols: (str, list) = None):
  """判断是否唯一"""
  if not key_cols:
    key_cols = df.columns.tolist()
  key_cols = ensure_list(key_cols)
  return not df.duplicated(subset=key_cols, keep=False).any()


def is_digit(x):
  if isinstance(x, bool):
    return False
  try:
    int(float(x))
    return True
  except (ValueError, TypeError):
    return False
