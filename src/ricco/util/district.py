from functools import cached_property

from ..base import not_empty
from ..base import warn_
from ..resource.bd_region import get_bd_region


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
