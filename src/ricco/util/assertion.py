import re
import warnings

import pandas as pd

from ..base import ensure_list
from ..base import not_empty
from .util import and_
from .util import is_digit
from .util import is_unique_series


def skip_column(df: pd.DataFrame, col: str, skip_if_not_exists: bool = True):
  df = df.copy().reset_index(drop=True)
  if col not in df:
    if skip_if_not_exists:
      warnings.warn(f'"{col}"列不存在，已跳过')
      return True
    else:
      raise KeyError(f'"{col}"列不存在')
  return False


def assert_columns_exists(df: pd.DataFrame, columns: list):
  """检查列是否存在"""
  df = df.copy().reset_index(drop=True)
  columns = ensure_list(columns)
  cols = [c for c in columns if c not in df]
  assert not cols, f'缺失"{cols}"列'


def assert_not_empty_str(df: pd.DataFrame,
                         col: str,
                         skip_if_not_exists: bool = True):
  """校验是否存在空白字符串"""
  df = df.copy().reset_index(drop=True)
  if skip_column(df, col, skip_if_not_exists):
    return
  assert '' not in df[col].values, f'"{col}"列存在空白字符串'


def assert_not_null(df: pd.DataFrame,
                    col: str,
                    skip_if_not_exists: bool = True):
  """检查是否非空（空白字符串认为是空值）"""
  df = df.copy().reset_index(drop=True)
  if skip_column(df, col, skip_if_not_exists):
    return
  if not isinstance(col, str):
    raise TypeError('col参数仅支持str类型')
  if df[col].isna().any():
    raise AssertionError(f'"{col}"列存在空值')
  assert_not_empty_str(df, col)


def assert_values_in(df: pd.DataFrame,
                     col: str,
                     enums: (dict, list),
                     skip_if_not_exists: bool = True):
  """
  检查Dataframe中某一列的值是否在指定的值的范围内

  Args:
    df: 要检查的dataframe
    col: 列名
    enums: 指定的enum值，当传入dict时，包含在key和value中的值都通过
    skip_if_not_exists: 当列不存在时是否跳过
  """
  df = df.copy().reset_index(drop=True)
  if skip_column(df, col, skip_if_not_exists):
    return
  if isinstance(enums, dict):
    vs = [*list(enums.keys()), *list(enums.values())]
  elif isinstance(enums, list):
    vs = enums
  else:
    raise TypeError('enums类型错误，list or dict')
  rv = [t for t in df[col].unique().tolist() if not_empty(t) and t not in vs]
  assert not rv, f'{rv}不是"{col}"列有效的enum值'


def assert_series_unique(df: pd.DataFrame,
                         columns: (str, list) = '名称',
                         text: str = '',
                         ignore_na=False):
  """
  检查并输出重复项

  Args:
    df: 要检查的Dataframe
    columns: 唯一的列
    text: 输出的文案
    ignore_na: 是否忽略空值，默认False，为True时，有空值的行不参与校验
  """
  df = df.copy().reset_index(drop=True)
  columns = ensure_list(columns)
  if not is_unique_series(df, columns, ignore_na=ignore_na):
    if ignore_na:
      df = df[and_(*[df[c].notna() for c in columns])]
    df = df[df.duplicated(subset=columns)][columns].sort_values(columns)
    df = df.drop_duplicates()
    ls = df.astype(str).to_dict('records')
    ls = [','.join(list(i.values())) for i in ls]
    info = '\n->'.join(ls)
    raise AssertionError(f'{text}{columns}列中存在重复值:\n->{info}')


def assert_series_digit(df: pd.DataFrame, col: str):
  """检查一列是否可以转为数值型"""
  df = df.copy().reset_index(drop=True)
  values = df[col].unique().tolist()
  rv = [i for i in values if not is_digit(i) and not_empty(i)]
  assert not rv, f'"{col}"列应为数值型，{rv}无法转换为数值型'


def assert_series_not_like(df: pd.DataFrame, col: str, pattern):
  """检查并输出符合正则表达式pattern的值"""
  df = df.copy().reset_index(drop=True)
  values = df[col].unique().tolist()
  rv = [i for i in values if re.match(pattern, str(i)) and not_empty(i)]
  assert not rv, f'异常的"{col}": {rv}'


def assert_subset(values: (list, set, tuple), superset: (list, set, tuple)):
  """检查values是否是superset的子集"""
  res = [i for i in values if i not in superset]
  assert not res, f'{res}不在指定的集合中'
