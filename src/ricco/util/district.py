from functools import cached_property

from ..base import not_empty
from ..base import warn_
from ..resource.bd_region import get_bd_region


def norm_city_name(name, full=False):
  """标准化城市名称为简称或全称"""
  df = get_bd_region()
  df = df[['城市名称', '城市简称']].drop_duplicates(ignore_index=True)
  df = df[
    (df['城市名称'] == name) |
    (df['城市简称'] == name)
    ].reset_index(drop=True)
  assert df.shape[0] == 1, f'未找到对应的城市或匹配到多个城市:{name}'
  return df['城市名称' if full else '城市简称'][0]


def get_city_id_by_name(name: str):
  df_o = get_bd_region()
  df = df_o[['城市id', '城市名称', '城市简称']].drop_duplicates()
  df = df.dropna()
  df = df[
    (df['城市简称'] == name) |
    (df['城市名称'] == name)
    ]
  assert df.shape[0] == 1, f'"{name}"匹配到多个或没有匹配到城市'
  return int(df['城市id'].unique().tolist()[0])


def get_upload_region(df, city):
  """从bd_region表中提取某个城市的区县数据，并处理成可以上传的格式"""
  city_id = df[
    (df['short_name'] == city) &
    (df['level_type'] == 2)
    ]['id'].unique().tolist()[0]
  df = df[df['parent_id'] == city_id]
  df = df[['id', 'name', 'geometry']]
  df.columns = ['regioncode', 'region', 'geometry']
  df = df.reset_index(drop=True)
  df['regioncode'] = df['regioncode'].astype(int)
  print(df.shape)
  return df


def get_upload_street(df, city):
  """从bd_region表中提取某个城市的街道数据，并处理成可以上传的格式"""
  city_id = df[
    (df['short_name'] == city) &
    (df['level_type'] == 2)
    ]['id'].unique().tolist()[0]
  region_ids = df[df['parent_id'] == city_id]['id'].tolist()
  df = df[df['parent_id'].isin(region_ids)]
  df = df[['id', 'name', 'parent_id', 'geometry']]
  df.columns = ['towncode', 'town', 'regioncode', 'geometry']
  df = df.reset_index(drop=True)
  df['towncode'] = df['towncode'].astype(int)
  df['regioncode'] = df['regioncode'].astype(int)
  print(df.shape)
  return df


class District:
  def __init__(self):
    """自动转换行政区划"""
    self.df = get_bd_region()

  @cached_property
  def city_list(self):
    """全部城市（全程+简称）列表"""
    city_list = [
      *self.df['城市名称'].unique().tolist(),
      *self.df['城市简称'].unique().tolist(),
    ]
    return [c for c in city_list if not_empty(c)]

  @cached_property
  def region_list(self):
    """全部区县（全程+简称）列表"""
    region_list = [
      *self.df['区县名称'].unique().tolist(),
      *self.df['区县简称'].unique().tolist(),
    ]
    return [r for r in region_list if not_empty(r)]

  def is_city(self, name: str) -> bool:
    """判断是否是地级市"""
    return name in self.city_list

  def is_region(self, name: str) -> bool:
    """判断是否是县市区"""
    return name in self.region_list

  def city_names(self, name: str):
    """返回匹配到的全部城市名称列表"""
    res = []
    for c in ['城市名称', '城市简称', '区县名称', '区县简称']:
      if name in self.df[c].unique():
        res = self.df[self.df[c] == name]['城市名称'].unique().tolist()
        break
    return res

  def province_names(self, name: str):
    """返回匹配到的全部省份名称列表"""
    res = []
    for c in ['省份名称', '省份简称', '城市名称', '城市简称', '区县名称',
              '区县简称']:
      if name in self.df[c].unique():
        res = self.df[self.df[c] == name]['省份名称'].unique().tolist()
        break
    return res

  def _get_district(self, name: str,
                    type_: str,
                    if_not_unique: str = None,
                    warning: bool = True):
    """
    通过地名（城市、区县）获取所在的城市名称

    Args:
      name: 城市名称
      type_: 城市、区县，可选参数city、province
      if_not_unique: 当查询到多个结果如何处理，
        - None， 默认， 返回空值
        - 'first'， 返回第一个
        - 'last'， 返回最后一个
        - 'all'， 返回所有城市的列表
      warning: 是否打印警告
    """
    assert if_not_unique in [None, 'first', 'last', 'all']
    if type_ == 'city':
      ls = self.city_names(name)
    elif type_ == 'province':
      ls = self.province_names(name)
    else:
      raise ValueError('type_ must be "city" or "province"')
    if ls:
      if len(ls) == 1:
        return ls[0]
      warn_(f'"{name}"匹配到多个城市{ls}', warning)
      if not if_not_unique:
        return
      if if_not_unique == 'first':
        return ls[0]
      if if_not_unique == 'last':
        return ls[-1]
      if if_not_unique == 'all':
        return ls

  def city(self, name: str, if_not_unique: str = None, warning: bool = True):
    """
    通过地名（城市、区县）获取所在的城市名称

    Args:
      name: 城市名称
      if_not_unique: 当查询到多个结果如何处理，
        - None， 默认， 返回空值
        - 'first'， 返回第一个
        - 'last'， 返回最后一个
        - 'all'， 返回所有城市的列表
      warning: 是否打印警告
    """
    return self._get_district(
        name=name,
        type_='city',
        if_not_unique=if_not_unique,
        warning=warning
    )

  def province(self, name, if_not_unique=None, warning=True):
    """
    通过地名（省份、城市、区县）获取所在的省份名称

    Args:
      name: 地名
      if_not_unique: 当查询到多个结果如何处理，
        - `None`， 默认， 返回空值
        - `first`， 返回第一个
        - `last`， 返回最后一个
        - 'all'， 返回所有省份的列表
      warning: 是否打印警告
    """
    return self._get_district(
        name=name,
        type_='province',
        if_not_unique=if_not_unique,
        warning=warning
    )

  def get_city_id_by_name(self, name: str):
    df = self.df[['城市id', '城市名称', '城市简称']].drop_duplicates()
    df = df.dropna()
    df = df[
      (df['城市简称'] == name) | (df['城市名称'] == name)
      ]
    assert df.shape[0] == 1, f'"{name}"匹配到多个或没有匹配到城市'
    return int(df['城市id'].unique().tolist()[0])
