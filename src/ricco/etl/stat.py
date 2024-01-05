import pandas as pd

from ..util.util import is_digit
from .transformer import round_by_columns

class_dic = {
  'count': '计数',
  'mean': '均值',
  'std': '标准差',
  'min': '最小值',
  'max': '最大值',
  '50%': '中位数',
}

skew_skurt = '''偏度（Skewness）

用来描述数据分布的对称性，正态分布的偏度为0。
计算数据样本的偏度，当偏度<0时，称为负偏，数据出现左侧长尾；
当偏度>0时，称为正偏，数据出现右侧长尾；当偏度为0时，表示数据相对均匀的分布在平均值两侧，
不一定是绝对的对称分布，此时要与正态分布偏度为0的情况进行区分。

当偏度绝对值过大时，长尾的一侧出现极端值的可能性较高。


峰度(Kurtosis)

用来描述数据分布陡峭或是平滑的情况。正态分布的峰度为3，
峰度越大，代表分布越陡峭，尾部越厚；
峰度越小，分布越平滑。
很多情况下，为方便计算，将峰度值－3，因此正态分布的峰度变为0，方便比较。

在方差相同的情况下，峰度越大，存在极端值的可能性越高。
'''


def describe_series(df: pd.DataFrame, col: str):
  """数值型列的描述性统计"""
  length = df.shape[0]
  df_desc = pd.DataFrame(df[col].describe().reset_index())
  df_desc = df_desc.rename(columns={'index': '分类', col: '值'})
  df_desc['分类'] = df_desc['分类'].replace(to_replace=class_dic)
  # 偏度系数和峰度系数
  skew_add = pd.DataFrame({
    '分类': '偏度系数',
    '值': [df[col].skew()],
  })
  kurt_add = pd.DataFrame({
    '分类': '峰度系数',
    '值': [df[col].kurt() - 3],
  })
  # 缺失数量和缺失率
  null_num = length - df_desc.loc[df_desc['分类'] == '计数', '值'][0]
  null_rate = null_num / length
  null_add = pd.DataFrame({'分类': '缺失数', '值': [null_num]})
  null_rate_add = pd.DataFrame({'分类': '缺失率', '值': [null_rate]})
  df_desc = pd.concat(
      [df_desc, skew_add, kurt_add, null_add, null_rate_add],
      ignore_index=True,
  )
  df_desc = round_by_columns(df_desc, ['值'])
  return df_desc


def describe_object(df: pd.DataFrame, col: str):
  """对文本列或枚举列进行描述统计"""
  desc = pd.DataFrame(df[col].value_counts().reset_index())
  if desc.shape[0] > 20:
    name = f'{col}_Top15'
    desc = desc.rename(columns={'index': name, col: '计数'})
    desc[name] = desc[name].replace(to_replace=class_dic)
    desc = desc.head(15)
  else:
    desc = desc.rename(columns={'index': col, col: '计数'})
    desc[col] = desc[col].replace(to_replace=class_dic)
  return desc


def describe_date(df: pd.DataFrame, col: str):
  """对日期列进行描述统计"""
  df = df[df[col].notna()].reset_index(drop=True)
  year_num = df[col].unique().shape[0]
  if year_num >= 3:
    df[col] = df[col].dt.strftime('%Y年')
    desc = pd.DataFrame(
        df[col].value_counts().sort_index().reset_index()
    )
    desc.columns = ['年份', '计数']
  else:
    df[col] = df[col].dt.strftime('%Y-%m')
    desc = pd.DataFrame(
        df[col].value_counts().sort_index().reset_index()
    )
    desc.columns = ['月份', '计数']
  return desc


def describe_auto(df: pd.DataFrame, col: str):
  """自动识别列的类型进行描述性统计"""
  _num = df[col].unique().shape[0]
  if df[col].dtype in (float, int) and _num > 10:
    return describe_series(df, col)
  if df[col].dtype not in (float, int):
    try:
      df[col] = pd.to_datetime(df[col])
    except ValueError:
      pass
  if df[col].dtype == 'datetime64[ns]':
    return describe_date(df, col)
  return describe_object(df, col)


def suspect_series_type(df: pd.DataFrame, col: str):
  """推断混合类型列的类型"""
  _r = 0.95
  length = df[df[col].notna()].shape[0]
  digit_num = df[df[col].apply(is_digit)].shape[0]
  if _r <= (rates := digit_num / length) < 1:
    return f'"{col}"列有超过{int(rates * 100)}%的值为"数值型"'

  date_num = df[pd.to_datetime(df[col], errors='coerce').notna()].shape[0]
  if _r <= (rates := date_num / length) < 1:
    return f' {col} 列有超过{int(rates * 100)}%的值为"日期格式"'
