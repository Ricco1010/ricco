import pandas as pd

from ..resource import P_BD_REGION
from ..util.decorator import singleton
from ..util.util import not_empty
from ..util.util import rstrip_d0

EX = ['新城区']


@singleton
def get_bd_region() -> pd.DataFrame:
  """获取bd_region表并转为宽表；同时保存为全局变量，避免多次IO"""
  df = pd.read_csv(P_BD_REGION)
  for c in ['parent_id', 'id']:
    df[c] = df[c].astype(str)
    df[c] = df[c].apply(rstrip_d0)
  df = df[df['parent_id'].notna()]
  df = df[df['level_type'].isin([1, 2, 3])]
  df['level_type'] = df['level_type'].replace(
      to_replace={1: '省份', 2: '城市', 3: '区县'}
  )
  # 区县
  df_region = df[df['level_type'] == '区县']
  df_region = df_region[['id', 'name', 'short_name', 'parent_id']]
  df_region.columns = ['区县id', '区县名称', '区县简称', '城市id']
  # 城市
  df_city = df[df['level_type'] == '城市']
  df_city = df_city[['id', 'name', 'short_name', 'parent_id']]
  df_city.columns = ['城市id', '城市名称', '城市简称', '省份id']
  # 省份
  df_prov = df[df['level_type'] == '省份']
  df_prov = df_prov[['id', 'name', 'short_name']]
  df_prov.columns = ['省份id', '省份名称', '省份简称']
  # 合并
  df_res = df_region.merge(df_city, how='outer', on='城市id')
  return df_res.merge(df_prov, how='outer', on='省份id')


@singleton
def cities():
  """城市列表，按照长度排序"""
  ls = get_bd_region()['城市名称'].unique().tolist()
  ls = [i for i in ls if not_empty(i)]
  return sorted(ls, key=lambda x: len(x), reverse=True)


@singleton
def regions():
  """区县列表，按照长度排序"""
  ls = get_bd_region()['区县名称'].unique().tolist()
  ls = [i for i in ls if not_empty(i) and i not in EX]
  return sorted(ls, key=lambda x: len(x), reverse=True)


@singleton
def city_region_list():
  """城市和区县列表，按照长度排序"""
  df = get_bd_region()
  ls = [*df['城市名称'].unique().tolist(), *df['区县名称'].unique().tolist()]
  ls = [i for i in ls if not_empty(i) and i not in EX]
  return sorted(ls, key=lambda x: len(x), reverse=True)
