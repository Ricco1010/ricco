import numpy as np
import pandas as pd

from ..base import ensure_list


def standard_e(df: pd.DataFrame, columns: list):
  """熵值法的正向指标的极差标准化"""
  df = df.copy()
  columns = ensure_list(columns)
  for c in columns:
    mmin = df[c].min()
    mmax = df[c].max()
    if mmin == mmax:
      df.loc[:, c] = None
    else:
      df.loc[:, c] = (df[c] - mmin) / (mmax - mmin)
  return df


def standard_e_neg(df: pd.DataFrame, columns: list):
  """熵值法的负向指标的极差标准化"""
  df = df.copy()
  columns = ensure_list(columns)
  for c in columns:
    mmin = df[c].min()
    mmax = df[c].max()
    if mmin == mmax:
      df.loc[:, c] = None
    else:
      df.loc[:, c] = (mmax - df[c]) / (mmax - mmin)
  return df


def pvalue(df: pd.DataFrame, columns: list):
  """计算指标下任一数值在该指标中的比重"""
  df = df.copy()
  columns = ensure_list(columns)
  for c in columns:
    df.loc[:, c] = df[c] / df[c].sum(axis=0)
  return df


def gevalue(df: pd.DataFrame, columns: list):
  """计算指标的差异系数"""
  df = df.copy()
  columns = ensure_list(columns)
  n = df.shape[0]
  for c in columns:
    df[c] = df.apply(lambda x: np.log(x[c]) * x[c], axis=1)
    j_sum = df[c].sum(axis=0)
    df.loc[:, c] = 1 - (-1 / np.log(n)) * j_sum
  return df


def wvalue(df, columns: list):
  """计算指标之间的权重关系"""
  df = df.copy()
  columns = ensure_list(columns)
  df_sum = df[columns].sum(axis=1)
  for c in columns:
    df.loc[:, c] = df[c] / df_sum
  return df


def entropy(df, columns: list = None):
  """
  采用熵值法计算的总分评价

  Args:
    df: 非负数化处理后的数据，默认其中数值量纲都是越大越好
    columns: 需要用熵值法计算权重的指标合集

  Returns:
    用过熵值法得到的总分, 权重
  """

  if not columns:
    columns = df.describe().columns.tolist()

  columns = ensure_list(columns)
  df = df[columns]
  df_p = pvalue(df, columns)
  df_g = gevalue(df_p, columns)
  df_w = wvalue(df_g, columns)
  x = (df_w * df_p).sum(axis=1)
  entropy_weight = df_w.median()
  return x, entropy_weight


def pca_score(df, columns: list = None):
  """PCA法计算器"""
  from sklearn.decomposition import PCA
  from sklearn.preprocessing import StandardScaler
  if not columns:
    columns = df.describe().columns.tolist()
  columns = ensure_list(columns)
  df = df[columns]
  scaler_std = StandardScaler()
  x_std = scaler_std.fit_transform(df)
  pca = PCA(n_components=1)
  x_reduced = pca.fit_transform(x_std)
  if (pca.components_[0] < 0).sum(0) == pca.components_[0].shape[0]:
    x_reduced = -x_reduced
  return x_reduced


class EntropyClass:
  def __init__(self, df, cols, neg_cols, key):
    """
    熵值法计算器-输出结果需要后续再进行rescale处理

    Args:
      df: 为原始待计算df
      cols: 需要参与计算的列名list
      neg_cols: cols中需要负向处理的列名
      key: 计算结果的列名

    Returns:
      entropy_res: 单独计算结果列
      entropy_df: 包含计算结果的df
      entropy_weight: 权重dict
    """
    df = standard_e(df, cols)
    df = standard_e_neg(df, neg_cols)
    df[key], self.entropy_weight = entropy(df, columns=cols)
    self.entropy_res = df[key]
    self.entropy_df = df


def rescale(
    df: pd.DataFrame,
    key: str,
    scale_min: float = 0,
    scale_max: float = 1,
    score_range: tuple = (0, 100)) -> pd.DataFrame:
  """
  归一化处理

  Args:
    df: 为原始待计算df
    key: 需要参与计算的列名
    scale_min: 下分位数, 低于该分位数的结果均取最小值
    scale_max: 上分位数, 高于该分位数的结果均取最大值
    score_range: 得分范围
  """
  from sklearn.preprocessing import MinMaxScaler
  scale_mm = MinMaxScaler(score_range)
  mmin = df[[key]].quantile(scale_min)[key]
  mmax = df[[key]].quantile(scale_max)[key]
  df.loc[df[key] < mmin, key] = mmin
  df.loc[df[key] > mmax, key] = mmax
  df_key = pd.DataFrame(scale_mm.fit_transform(df[[key]]),
                        index=df.index,
                        columns=[key])
  return df_key[key]
