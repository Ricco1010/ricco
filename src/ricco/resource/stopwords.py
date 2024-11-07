from functools import lru_cache

import pandas as pd

from . import P_STOPWORDS


@lru_cache()
def get_stopwords() -> list:
  """获取停词表列表"""
  print('获取停词表')
  df = pd.read_csv(P_STOPWORDS, header=None)
  return df[0].tolist()
