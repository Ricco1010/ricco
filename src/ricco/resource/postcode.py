from functools import lru_cache

import pandas as pd

from . import P_POSTCODE


@lru_cache()
def get_postcode() -> pd.DataFrame:
  """获取邮编数据集；并进行缓存避免多次IO"""
  print('获取邮编数据集')
  df = pd.read_csv(
      P_POSTCODE,
      dtype=str,
      usecols=['province', 'city', 'county', 'postcode']
  )
  df = df.dropna(subset='postcode')
  df = df.drop_duplicates(subset='postcode', ignore_index=True)
  return df
