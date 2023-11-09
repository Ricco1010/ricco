import logging
import warnings

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


def ensure_ext(ext: str):
  if isinstance(ext, str) and ext != '' and not ext.startswith('.'):
    return '.' + ext
  return ext


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


def second_to_dhms(second):
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


def second_to_desc(second):
  """将秒转为时间描述"""
  d, h, m, second = second_to_dhms(second)
  if d + h + m == 0:
    return f'{second:.2f}s'
  if d + h == 0:
    return f'{m}m {second:.0f}s'
  if d == 0:
    return f'{h}h {m}m {second:.0f}s'
  return f'{d}d {h}h {m}m {second:.0f}s'


def warn_(msg, if_or_not=True, mode='warning'):
  if if_or_not:
    if mode == 'warning':
      warnings.warn(msg)
    if mode == 'logging':
      logging.warning(msg)
