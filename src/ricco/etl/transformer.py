import warnings
from datetime import datetime

import numpy as np
import pandas as pd
from .graph import query_from_graph
from ..util.assertion import assert_series_unique
from ..util.decorator import progress
from ..util.decorator import timer
from ..util.util import and_
from ..util.util import ensure_list
from ..util.util import fuzz_match
from ..util.util import is_empty
from ..util.util import list2dict
from ..util.util import to_float


def best_unique(df: pd.DataFrame,
                key_cols: (list, str),
                value_cols: (str, list) = None,
                filter_cols=False,
                drop_if_null=None) -> pd.DataFrame:
  """
  优化的去重函数：
    为保证数据的完整性，去重时优先去除指定列中的空值
  Args:
    df:
    key_cols: 按照哪些列去重
    value_cols: 优先去除那些列的空值，该列表是有顺序的
    filter_cols: 是否只保留key_cols和value_cols里面的列，默认False
    drop_if_null: 如何处理value_cols内值为空的列；'all'：都为空时删除该列，'any'：任意一列为空时就删除，None：保留空白
  """
  warnings.warn('即将弃用，请使用keep_best_unique', DeprecationWarning)
  key_cols = ensure_list(key_cols)
  if not value_cols:
    value_cols = [i for i in df.columns if i not in key_cols]
  value_cols = ensure_list(value_cols)
  if drop_if_null:
    df = df.dropna(
        subset=value_cols,
        how=drop_if_null
    ).dropna(
        subset=key_cols,
        how='all')
  df = df.sort_values(value_cols, na_position='first')
  df = df.drop_duplicates(key_cols, keep='last', ignore_index=True)
  if filter_cols:
    df = df[key_cols + value_cols]
  return df


def keep_best_unique(df: pd.DataFrame,
                     subset: (list, str),
                     value_cols: (str, list) = None
                     ) -> pd.DataFrame:
  """
  优化的去重函数，为保证数据的完整性，去重时优先去除指定列中的空值
  Args:
    df: 要去重的Dataframe
    subset: 按照哪些列去重
    value_cols: 优先去除那些列的空值，该列表是有顺序的
  """
  subset = ensure_list(subset)

  if not value_cols:
    value_cols = [i for i in df if i not in subset]
  value_cols = ensure_list(value_cols)

  return df.sort_values(
      value_cols, na_position='first'
  ).drop_duplicates(
      subset, keep='last'
  ).sort_index()


def table2dict(df: pd.DataFrame,
               key_col: str = None,
               value_col: (str, list) = None,
               orient: str = 'dict') -> dict:
  """
  DataFrame转字典
  Args:
    df:
    key_col: 生成key的列
    value_col: 生成value的列
    orient: 生成dict的方式，默认'dict',还有 ‘list’, ‘series’, ‘split’, ‘records’, ‘index’
  """
  if not all([key_col, value_col]):
    columns = df.columns.tolist()
    key_col = columns[0]
    value_col = columns[1]
  df = df[df[key_col].notna()].set_index(key_col)
  if isinstance(value_col, list):
    df = df[value_col]
    return df.to_dict(orient=orient)
  else:
    df = df[[value_col]]
    return df.to_dict(orient=orient)[value_col]


def round_by_columns(df, columns: list):
  """对整列进行四舍五入，默认绝对值大于1的数值保留两位小数，小于1 的保留4位"""

  def _round(x):
    if is_empty(x):
      return np.nan
    if abs(x) >= 1:
      return round(x, 2)
    return round(x, 4)

  columns = ensure_list(columns)
  for c in columns:
    df[c] = df[c].apply(lambda x: _round(x))
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
              overwrite: bool = True,
              errors: str = 'ignore') -> pd.DataFrame:
  """
  根据某一列更新dataframe里的数据
  Args:
    df: 待升级的数据集
    new_df: 用于更新的DataFrame
    on: （可选参数）用于判断更新哪些行的列
    overwrite : （可选参数）控制如何处理原DataFrame在重叠位置上 **非空** 的值，默认为True

      * True: 默认值；使用 `other` DataFrame中的值覆盖原DataFrame中相应位置的值.
      * False: 只更新原DataFrame中重叠位置数据为 *空* 的值.
    errors: （可选参数）控制如何处理两个DataFrame同一位置都有值的行为，默认为'ignore'

      * 'ignore': 默认值；DataFrame类型 df和other在同一个cell位置都是非NA值，
        使用other中的值替换df中的值。
      * 'raise': target和other都在同一位置包含非NA数据将抛出ValueError异常（'Data overlaps'）。
  """
  if on:
    df.set_index(on, inplace=True)
    df.update(new_df.set_index(on), overwrite=overwrite, errors=errors)
    df.reset_index(inplace=True)
  else:
    df.update(new_df, overwrite=overwrite, errors=errors)
  return df


def date_to(series: pd.Series, mode: str = 'first') -> pd.Series:
  """
  将日期转为当月的第一天或最后一天
  Args:
    series: pd.Series
    mode: 'first' or 'last'
  """
  from pandas.tseries.offsets import MonthEnd

  def trans(x):
    if x is not pd.NaT:
      y = int(x.year)
      m = int(x.month)
      d = int(x.day)
      return datetime(y, m, d)
    else:
      return

  assert mode in ('first', 'last'), "可选参数为first or last"
  series = pd.to_datetime(series)
  if mode == 'first':
    series = series.apply(lambda x: x.replace(day=1))
  else:
    series = pd.to_datetime(series, format="%Y%m") + MonthEnd(1)
  return series.apply(trans)


@progress
def fuzz_df(df: pd.DataFrame,
            col: str,
            target_series: (list, pd.Series),
            c_dst=None) -> pd.DataFrame:
  """
  模糊匹配。为DataFrame中的某一列从某个集合中模糊匹配匹配相似度最高的元素
  Args:
    df: 输入的dataframe
    col: 要匹配的列
    target_series: 从何处匹配， list/pd.Series
    c_dst: 关联后输出的列名，默认为原列名+"_target"后缀
  """
  if not c_dst:
    c_dst = f'{col}_target'

  df_temp = df[[col]].drop_duplicates(ignore_index=True)

  df_temp[[
    c_dst, 'normal_score', 'partial_score'
  ]] = df_temp.progress_apply(
      lambda r: fuzz_match(r[col], target_series),
      result_type='expand',
      axis=1)
  return df.merge(df_temp, on=col, how='left')


def series_to_float(series: pd.Series, rex_method: str = 'mean') -> pd.Series:
  """
  pandas.Series: str --> float
  Args:
    series: 要转换的pandas列
    rex_method: 计算mean,max,min， 默认为mean
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


@timer
@progress
def expand_dict(df, c_src):
  """展开字典为多列"""
  return pd.concat(
      [
        df.drop(c_src, axis=1),
        df[c_src].progress_apply(
            lambda x: pd.Series(x, dtype='object')
        ).set_index(df.index)
      ],
      axis=1
  )


@progress
@timer
def split_list_to_row(df: pd.DataFrame, column):
  """将列表列中列表的元素拆成多行"""
  if pd.__version__ >= '1.3.0':
    return df.explode(column, ignore_index=True)
  df[column] = df[column].progress_apply(list2dict)
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


def is_unique(df: pd.DataFrame, key_cols: (str, list) = None):
  """判断是否唯一"""
  warnings.warn(
      '方法即将停用，请使用"ricco.util.util.is_unique_series"方法替代',
      DeprecationWarning
  )
  if not key_cols:
    key_cols = df.columns.to_list()
  key_cols = ensure_list(key_cols)
  return not df.duplicated(subset=key_cols, keep=False).any()


def one_line(df, key_cols, key_value, value_cols):
  """获取一行重置索引后的数据"""
  cond = and_(*[df[c] == key_value[c] for c in key_cols])
  df = df[cond][[*key_cols, *value_cols]]
  return df.reset_index(drop=True)


@timer
def is_changed(df_old: pd.DataFrame,
               df_new: pd.DataFrame,
               key_cols: (str, list) = None,
               value_cols: (str, list) = None,
               c_res: str = 'is_changed') -> pd.DataFrame:
  """
  判断新旧数据集中的每一条数据是否变化
  Args:
    df_old: 原始数据集
    df_new: 修改后的数据集
    key_cols: 关键列，不指定则以索引列为准
    value_cols: 要对比的列，默认出key_cols之外的其他列
    c_res: 对比结果列名，默认为“is_changed”
  """
  # 数据集及参数检验
  key_cols = ensure_list(key_cols)
  assert_series_unique(df_new, key_cols)
  if not value_cols:
    error_msg = 'Each datasets must have same columns.'
    assert set(df_new.columns) == set(df_old.columns), error_msg
    value_cols = [c for c in df_old if c not in key_cols]
  # 对比
  # 默认所有的都是更改的
  df_new = df_new.copy()
  df_new[c_res] = 'Changed'
  df_temp = df_old[[*key_cols, *value_cols]].merge(
      df_new[[*key_cols, *value_cols, c_res]],
      how='left',
      on=key_cols)
  # 合并后为空的为 NotFound
  df_temp[c_res] = df_temp[c_res].fillna('NotFound')

  # 对比每一个值，如果每一列的每一个值都相同，则认为是没有变化
  cond = and_(
      *[
        (df_temp[f'{c}_x'] == df_temp[f'{c}_y']) |
        (df_temp[f'{c}_x'].isna() & df_temp[f'{c}_y'].isna())
        for c in value_cols
      ]
  )
  df_temp.loc[cond, c_res] = 'NotChange'
  df_temp = df_temp[[*key_cols, c_res]]
  return df_old.merge(df_temp, how='left', on=key_cols)


def df_iter(df: pd.DataFrame, *, chunksize: int = None, parts: int = None):
  """
  DataFrame切片生成器
  Args:
    df: 要切片的DataFrame
    chunksize: 每次返回的大小，与parts必须指定一个
    parts: 返回的次数，与chunksize必须指定一个
  """
  assert any([chunksize, parts]), 'chunksize和parts必须指定一个'
  size = df.shape[0]
  if chunksize:
    parts = int(size / chunksize) + 1
  else:
    chunksize = int(size / parts) + 1
  for i in range(parts):
    low = i * chunksize
    high = (i + 1) * chunksize
    if i == parts - 1:
      yield df.iloc[low:, :]
    else:
      yield df.iloc[low: high, :]


def create_columns(df: pd.DataFrame, columns: list, value=None):
  """
  创建新的列，默认为空
  Args:
    df: DataFrame
    columns: 列名
    value: 值，默认为空
  """
  columns = ensure_list(columns)
  for c in columns:
    if c not in df:
      df[c] = value
  return df


@progress
def expand_graph(df: pd.DataFrame,
                 start_level,
                 c_key='id',
                 c_level_type='level_type',
                 c_parent_key='parent_id',
                 c_info=None):
  """
  将图数据展开为宽表
  Args:
    df: 要展开的图数据
    start_level: 开始展开的层级，一般是最低层级
    c_key: 关键列
    c_level_type: 层级类型列
    c_parent_key: 父级关键列
    c_info: 要保留的其他列
  """
  assert start_level in df[c_level_type].unique(), 'start_level不在level_type中'
  df_base = df.copy()
  graph_df = df.copy()
  graph_df[c_level_type] = graph_df[c_level_type].apply(
      lambda lp: f'{lp}_{c_key}'
  )
  df = df[df[c_level_type] == start_level]
  df = df[[c_key]].reset_index(drop=True)
  df['extra'] = df[c_key].progress_apply(
      lambda x: query_from_graph(
          key=x, graph_df=graph_df, c_key=c_key,
          c_level_type=c_level_type, c_parent_key=c_parent_key)
  )
  df = expand_dict(df, 'extra')
  if c_info:
    c_info = ensure_list(c_info)
    for level_type in df_base[c_level_type].unique():
      df_level = df_base[[c_key, *c_info]]
      df_level.columns = [f'{level_type}_{c}' for c in df_level]
      if f'{level_type}_{c_key}' in df_level:
        df = df.merge(df_level, on=f'{level_type}_{c_key}', how='left')
  return df
