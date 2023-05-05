from datetime import datetime

import pandas as pd

from ..util.geom import wkb_loads
from ..util.util import ensure_list
from ..util.util import fuzz_match
from ..util.util import list2dict
from ..util.util import to_float


def filter_valid_geom(df: pd.DataFrame,
                      c_geometry='geometry',
                      ignore_index=True):
  """仅保留有效的geometry，剔除空白和错误的geometry行"""
  if 'temp_xxx' in df.columns:
    raise KeyError('数据集中不能存在【temp_xxx】列')
  df['temp_xxx'] = df[c_geometry].apply(wkb_loads)
  df = df[df['temp_xxx'].notna()]
  if ignore_index:
    df = df.reset_index(drop=True)
  del df['temp_xxx']
  return df


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


def standard(series: (pd.Series, list),
             q: float = 0.01,
             min_score: float = 0,
             minus: bool = False) -> (pd.Series, list):
  if minus:
    series = 1 / (series + 1)
  max_ = series.quantile(1 - q)
  min_ = series.quantile(q)
  series = series.apply(
      lambda x: (x - min_) / (max_ - min_) * (100 - min_score) + min_score)
  series[series >= 100] = 100
  series[series <= min_score] = min_score
  return series


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


def date_to(series: pd.Series, mode: str = 'first') -> pd.Series:
  """
  将日期转为当月的第一天或最后一天

  :param series: pd.Serise
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

  series = pd.to_datetime(series)
  if mode == 'first':
    series = series.apply(lambda x: x.replace(day=1))
  elif mode == 'last':
    series = pd.to_datetime(series, format="%Y%m") + MonthEnd(1)
  else:
    raise ValueError(f"{mode}不是正确的参数，请使用 'first' or 'last'")
  return series.apply(trans)


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


def series_to_float(series: pd.Series, rex_method: str = 'mean') -> pd.Series:
  """
  pandas.Series: str --> float

  :param series: 要转换的pandas列
  :param rex_method: 计算mean,max,min， 默认为mean
  """
  return series.apply(lambda x: to_float(x, rex_method=rex_method))


def filter_by_df(df: pd.DataFrame, sizer: pd.DataFrame) -> pd.DataFrame:
  """根据一个dataframe筛选另一个dataframe"""
  sizer = sizer.drop_duplicates()
  cond = False
  for i in sizer.index:
    _cond = True
    for c in sizer:
      value = sizer[c][i]
      if pd.isna(value):
        _cond = _cond & df[c].isna()
      else:
        _cond = _cond & (df[c] == value)
    cond = cond | _cond
  return df[cond]


def expand_dict(df, c_src):
  """展开字典为多列"""
  return pd.concat(
      [
        df.drop(c_src, axis=1),
        df[c_src].apply(
            lambda x: pd.Series(x, dtype='object')
        ).set_index(df.index)
      ],
      axis=1
  )


def split_list_to_row(df, column):
  """将列表列中列表的元素拆成多行"""
  df[column] = df[column].apply(list2dict)
  return df.drop(columns=column).join(
      expand_dict(
          df[[column]], column
      ).stack(
      ).reset_index(
          level=1, drop=True
      ).rename(column)
  )


def dict2df(data: dict, c_key='key', c_value='value', as_index=False):
  """将字典转为dataframe"""
  df = pd.DataFrame()
  df[c_key] = data.keys()
  df[c_value] = data.values()
  if as_index:
    df.set_index(c_key, inplace=True)
  return df
