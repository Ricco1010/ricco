from functools import lru_cache

from ricco import is_empty

from ..base import warn_
from ..resource.postcode import get_postcode
from .district import norm_city_name


@lru_cache()
def postcode_city_mapping():
  """
  获取邮编与城市名称的映射关系
  """
  df = get_postcode()[['postcode', 'city']]
  df = df.dropna()
  df = df.drop_duplicates(subset=['postcode'])
  df = df.set_index('postcode')
  return df.to_dict()['city']


@lru_cache()
def get_city_from_postcode(postcode: str, full=False, warning=False):
  """
  根据邮编获取城市名称

  Args:
    postcode: 邮编
    full: 是否返回全称
    warning: 是否打印警告
  """
  if is_empty(postcode):
    return
  if isinstance(postcode, (float, int)):
    postcode = str(int(postcode))
    postcode = postcode.zfill(6)
  if not isinstance(postcode, str) or len(postcode) != 6:
    warn_(f'邮编{postcode}必须为字符串且长度为6', if_or_not=warning)
    return
  mapping = postcode_city_mapping()
  city = mapping.get(postcode)
  if city:
    return norm_city_name(city, full=full)
