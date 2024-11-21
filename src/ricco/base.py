import logging
import warnings
from datetime import datetime

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
  if isinstance(val, pd.Series):
    return val.tolist()
  return [val]


def ensure_ext(ext: str):
  """
  规范文件扩展名，保持扩展名为点(.)开头

  Examples:
    >>> ensure_ext('csv')
    '.csv'
  """
  if isinstance(ext, str) and ext != '' and not ext.startswith('.'):
    return '.' + ext
  return ext


def is_empty(x) -> bool:
  """
  判断变量是否为空值

  以下值认为是空白：
    - 空白列表、字典, 如：`[]`, `{}`
    - 空白Dataframe、Series, 如：`pd.DataFrame()`
    - 空白shapely格式的geometry，如：`Point(np.nan, np.nan)`
  """
  if isinstance(x, (list, dict, tuple)):
    return False if x else True
  if isinstance(x, (pd.DataFrame, pd.Series)):
    return x.empty
  if isinstance(x, BaseGeometry):
    return x.is_empty
  return pd.isna(x)


def not_empty(x) -> bool:
  """判断是否非空，对`is_empty`取反"""
  return not is_empty(x)


def second_to_dhms(second) -> tuple:
  """将秒转为天、时、分、秒"""
  d = int(second // 86400)
  second = second % 86400
  h = int(second // 3600)
  second = second % 3600
  m = int(second // 60)
  second = second % 60
  if d + h + m == 0:
    second = round(second, 2)
  else:
    second = int(second)
  return d, h, m, second


def second_to_desc(second) -> str:
  """
  将秒转为时间描述

  Examples:
    >>> second_to_desc(123)
    '2m 3s'
    >>> second_to_desc(1234)
    '20m 40s'
    >>> second_to_desc(123456)
    '1d 10h 17m 36s'
  """
  d, h, m, second = second_to_dhms(second)
  if d + h + m == 0:
    return f'{second:.2f}s'
  if d + h == 0:
    return f'{m}m {second:.0f}s'
  if d == 0:
    return f'{h}h {m}m {second:.0f}s'
  return f'{d}d {h}h {m}m {second:.0f}s'


def log(msg):
  """打印带有时间的日志信息"""
  t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  logging.warning(f'{t} {msg}')


def warn_(msg, if_or_not=True, mode='warning'):
  """
  打印警告信息，嵌入函数内部，可由if_or_not控制是否打印

  Args:
    msg: 要输出的警告信息
    if_or_not: 是否输出
    mode: 警告类型，支持logging和warning
  """
  if if_or_not:
    if mode == 'warning':
      warnings.warn(msg)
    if mode == 'logging':
      log(msg)


def agg_parser(agg: dict) -> list:
  """将字典形式的agg聚合参数转换为[原字段名，计算函数，储存字段名]列表形式"""
  res = []
  for c, functions in agg.items():
    functions = ensure_list(functions)
    for func in functions:
      res.append([c, func, f'{c}_{func}'])
  return res
