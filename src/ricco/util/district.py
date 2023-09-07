import warnings

import pandas as pd

from ..resource import P_BD_REGION
from .util import rstrip_d0


def bd_region_process(df: pd.DataFrame) -> pd.DataFrame:
  """将bd_region展开为方便查询的宽表"""
  for c in ['parent_id', 'id']:
    df[c] = df[c].astype(str)
    df[c] = df[c].apply(rstrip_d0)
  df = df[df['parent_id'].notna()]
  df = df[df['level_type'].isin([2, 3])]
  df['level_type'] = df['level_type'].replace(to_replace={2: '城市', 3: '区县'})
  df_region = df[df['level_type'] == '区县']
  df_region = df_region[['id', 'name', 'short_name', 'parent_id']]
  df_region.columns = ['区县id', '区县名称', '区县简称', '城市id']
  df_city = df[df['level_type'] == '城市']
  df_city = df_city[['id', 'name', 'short_name']]
  df_city.columns = ['城市id', '城市名称', '城市简称']
  return df_region.merge(df_city, how='outer', on='城市id')


def get_bd_region() -> pd.DataFrame:
  """获取bd_region表并转为宽表；同时保存为全局变量，避免多次IO"""
  if '__data_from_region' not in globals():
    global __df_bd_region
    __df_bd_region = pd.read_csv(P_BD_REGION)
    __df_bd_region = bd_region_process(__df_bd_region)
  return __df_bd_region


class District:
  def __init__(self):
    self.df = get_bd_region()

  def city_names(self, name):
    res = []
    for c in ['城市名称', '城市简称', '区县名称', '区县简称']:
      if name in self.df[c].unique():
        res = self.df[self.df[c] == name]['城市名称'].unique().tolist()
        break
    return res

  def city(self, name, if_not_unique=None, warning=True):
    """
    通过城市或区县名称获取所在的城市名称
    Args:
      name: 城市名称
      if_not_unique: 当查询到多个结果如何处理，
        - None， 默认， 返回空值
        - 'first'， 返回第一个
        - 'last'， 返回最后一个
        - 'all'， 返回所有城市的列表
      warning: 是否打印警告
    Returns:
      城市名称
    """
    assert if_not_unique in [None, 'first', 'last', 'all']
    city_list = self.city_names(name)
    if city_list:
      if len(city_list) == 1:
        return city_list[0]
      if warning:
        warnings.warn(f'"{name}"匹配到多个城市{city_list}')
      if not if_not_unique:
        return
      if if_not_unique == 'first':
        return city_list[0]
      if if_not_unique == 'last':
        return city_list[-1]
      if if_not_unique == 'all':
        return city_list
