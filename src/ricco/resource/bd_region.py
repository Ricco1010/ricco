from functools import lru_cache

import pandas as pd

from ..base import not_empty
from ..util.util import rstrip_d0
from . import P_BD_REGION

EX = ['新城区']


@lru_cache()
def get_bd_region(start_level='区县') -> pd.DataFrame:
  """获取bd_region表并转为宽表；同时保存为全局变量，避免多次IO"""
  print('获取行政区划数据集')
  default_level = ['街镇', '区县', '城市', '省份']
  levels = default_level[default_level.index(start_level):]

  df = pd.read_csv(P_BD_REGION)
  for c in ['parent_id', 'id']:
    df[c] = df[c].astype(str)
    df[c] = df[c].apply(rstrip_d0)
  df = df[df['parent_id'].notna()]
  df = df[df['level_type'].isin([1, 2, 3, 4])]
  df['level_type'] = df['level_type'].replace(
      to_replace={1: '省份', 2: '城市', 3: '区县', 4: '街镇'}
  )

  df_prov = df[df['level_type'] == '省份']
  df_prov = df_prov[['id', 'name', 'short_name']]
  df_prov.columns = ['省份id', '省份名称', '省份简称']
  dfs = {
    '省份': df_prov.copy()
  }

  for i, l in enumerate(levels[:-1]):
    _df = df[df['level_type'] == l]
    _df = _df[['id', 'name', 'short_name', 'parent_id']]
    _df.columns = [f'{l}id', f'{l}名称', f'{l}简称', f'{levels[i + 1]}id']
    dfs[l] = _df.copy()

  df_res = dfs[levels[0]]
  for i in range(len(levels) - 1):
    df_res = df_res.merge(
        dfs[levels[i + 1]],
        on=f'{levels[i + 1]}id',
        how='outer',
    )
  return df_res


@lru_cache()
def cities():
  """城市列表，按照长度排序"""
  ls = get_bd_region()['城市名称'].unique().tolist()
  ls = [i for i in ls if not_empty(i)]
  return sorted(ls, key=lambda x: len(x), reverse=True)


@lru_cache()
def regions():
  """区县列表，按照长度排序"""
  ls = get_bd_region()['区县名称'].unique().tolist()
  ls = [i for i in ls if not_empty(i) and i not in EX]
  return sorted(ls, key=lambda x: len(x), reverse=True)


@lru_cache()
def city_region_list():
  """城市和区县列表，按照长度排序"""
  df = get_bd_region()
  ls = [*df['城市名称'].unique().tolist(), *df['区县名称'].unique().tolist()]
  ls = [i for i in ls if not_empty(i) and i not in EX]
  return sorted(ls, key=lambda x: len(x), reverse=True)
