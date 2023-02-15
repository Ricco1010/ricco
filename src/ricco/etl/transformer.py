from datetime import datetime

import pandas as pd

from ..util import ensure_list
from ..util import fuzz_match
from ..util import to_float


def best_unique(df: pd.DataFrame,
                key_cols: (list, str),
                value_cols: (str, list) = None,
                filter=False,
                drop_if_null='all'):
  """
  优化的去重函数：
    为保证数据的完整性，去重时优先去除指定列中的空值

  :param df:
  :param key_cols: 按照哪些列去重
  :param value_cols: 优先去除那些列的空值，该列表是有顺序的
  :param filter:
  :param drop_if_null: 如何处理value_cols内值为空的列；'all'：都为空时删除该列，'any'：任意一列为空时就删除，None：保留空白
  :return:
  """
  key_cols = ensure_list(key_cols)
  if value_cols is None:
    value_cols = [i for i in df.columns if i not in key_cols]
  else:
    value_cols = ensure_list(value_cols)
  if drop_if_null is not None:
    df = df.dropna(subset=value_cols, how=drop_if_null).dropna(subset=key_cols,
                                                               how='all')
  df = df.sort_values(value_cols, na_position='first')
  df = df.drop_duplicates(key_cols, keep='last').reset_index(drop=True)
  if filter:
    df = df[key_cols + value_cols]
  return df


def table2dict(df: pd.DataFrame,
               key_col: str = None,
               value_col: (str, list) = None,
               orient: str = 'dict') -> dict:
  """
  DataFrame转字典

  :param df:
  :param key_col: 生成key的列
  :param value_col: 生成value的列
  :param orient: 生成dict的方式，默认'dict',还有 ‘list’, ‘series’, ‘split’, ‘records’, ‘index’
  :return:
  """
  if (key_col is None) or (value_col is None):
    cols = list(df.columns).copy()
    key_col = cols[0]
    value_col = cols[1]

  df = df[~df[key_col].isna()]
  df.set_index(key_col, inplace=True)

  if isinstance(value_col, list):
    df = df[value_col]
    return df.to_dict(orient=orient)
  else:
    df = df[[value_col]]
    return df.to_dict(orient=orient)[value_col]


def round_by_columns(df, col: list):
  """对整列进行四舍五入，默认绝对值大于1的数值保留两位小数，小于1 的保留4位"""

  def _round(x):
    if abs(x) >= 1:
      return round(x, 2)
    else:
      return round(x, 4)

  col = ensure_list(col)
  for i in col:
    df[i] = df[i].apply(lambda x: _round(x))
  return df


def standard(serise: (pd.Series, list),
             q: float = 0.01,
             min_score: float = 0,
             minus: bool = False) -> (pd.Series, list):
  if minus:
    serise = 1 / (serise + 1)
  max_ = serise.quantile(1 - q)
  min_ = serise.quantile(q)
  serise = serise.apply(
      lambda x: (x - min_) / (max_ - min_) * (100 - min_score) + min_score)
  serise[serise >= 100] = 100
  serise[serise <= min_score] = min_score
  return serise


def update_df(df: pd.DataFrame,
              new_df: pd.DataFrame,
              on: (str, list) = None,
              mode='update'):
  """
  根据某一列更新dataframe里的数据

  :param df: 待升级的
  :param new_df: 新表
  :param on: 根据哪一列升级,默认为None，使用index
  :param mode：处理方式，update：直接更新对应位置的数值，insert：只有对应位置为空时才更新
  :return:
  """
  v1 = len(df)
  if on is not None:
    on = ensure_list(on)
    new_df = new_df.drop_duplicates()
    if any(new_df[on].duplicated()):
      raise ValueError('new_df中有重复的索引列对应不同的值，请检查')
    new_df = df[on].drop_duplicates().merge(new_df, how='inner', on=on)
    df = df.set_index(on, drop=False)
    new_df = new_df.set_index(on, drop=False)
  if mode == 'update':
    df.update(new_df)
  elif mode == 'insert':
    df = df.combine_first(new_df)
  else:
    raise ValueError(f'参数{mode}错误,可选参数为 update or insert')
  df = df.reset_index(drop=True)
  if on is not None:
    if v1 != len(df):
      raise ValueError('update后Dataframe结构发生变化，请检查')
  return df


def date_to(serise: pd.Series, mode: str = 'first'):
  """
  将日期转为当月的第一天或最后一天

  :param serise: pd.Serise
  :param mode: 'first' or 'last'
  :return:
  """
  from pandas.tseries.offsets import MonthEnd

  def trans(x):
    if x is not pd.NaT:
      y = int(x.year)
      m = int(x.month)
      d = int(x.day)
      return datetime(y, m, d)
    else:
      return None

  serise = pd.to_datetime(serise)
  if mode == 'first':
    serise = serise.apply(lambda x: x.replace(day=1))
  elif mode == 'last':
    serise = pd.to_datetime(serise, format="%Y%m") + MonthEnd(1)
  else:
    raise ValueError(f"{mode}不是正确的参数，请使用 'first' or 'last'")
  serise = serise.apply(trans)
  return serise


def fuzz_df(df: pd.DataFrame,
            col: str,
            target_serise: (list, pd.Series)) -> pd.DataFrame:
  """
  为DataFrame中的某一列，从某个集合中匹配相似度最高的元素

  :param df: 输入的dataframe
  :param col: 要匹配的列
  :param target_serise: 从何处匹配， list/pd.Serise
  :return:
  """
  df[[f'{col}_target',
      'normal_score',
      'partial_score']] = df.apply(lambda x: fuzz_match(x[col], target_serise),
                                   result_type='expand', axis=1)
  return df


def serise_to_float(serise: pd.Series, rex_method: str = 'mean'):
  """
  pandas.Series: str --> float

  :param serise: 要转换的pandas列
  :param rex_method: 计算mean,max,min， 默认为mean
  """
  return serise.apply(lambda x: to_float(x, rex_method=rex_method))
