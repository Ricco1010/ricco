import logging
import re
import uuid
import warnings

import numpy as np
import pandas as pd


def ensure_list(val):
  """将标量值和Collection类型都统一转换为LIST类型"""
  if val is None:
    return []
  if isinstance(val, list):
    return val
  if isinstance(val, (set, tuple)):
    return list(val)
  return [val]


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
  if pd.isna(s):
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
  lis2 = [getattr(np, num_type)(per2float(i)) for i in lis]
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
  from ricco.config import UTIL_CN_NUM

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


def first_notnull_value(series):
  for v in series:
    if pd.notna(v):
      return v
  warnings.warn('所有值均为空值')
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
  from ricco.config import CITY_IDS
  city_id = CITY_IDS.get(city if city.endswith('市') else f'{city}市')
  if not city_id:
    logging.warning('获取城市code失败，请在config.py中确认补充该城市')
  return city_id
