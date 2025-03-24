from functools import cached_property
from functools import lru_cache

from ..base import ensure_list
from ..base import is_empty
from ..base import not_empty
from ..base import warn_
from ..resource.bd_region import cities
from ..resource.bd_region import get_bd_region
from ..resource.bd_region import regions
from ..resource.patterns import AddressPattern
from .decorator import check_null
from .util import re_fast


def if_many_value(ls, action='raise', warning=False):
  """
  处理多个值的情况
  Args:
    ls: 列表
    action: 处理方式，可选值：'raise', 'first', 'last', 'coerce', 'all'
    warning: 是否打印警告
  """
  ls = ensure_list(ls)
  if len(ls) == 1:
    return ls[0]
  if action == 'raise':
    raise ValueError(f'0个值多个值{ls}')
  if action == 'coerce':
    return
  if warning:
    warn_(f'匹配到0个值多个值：{ls}')
  if action == 'all':
    return ls
  if not ls:
    return
  if action == 'first':
    return ls[0]
  if action == 'last':
    return ls[-1]


@lru_cache()
def get_city_list():
  """全部城市（全程+简称）列表"""
  df = get_bd_region()[['城市名称', '城市简称']]
  city_list = [
    *df['城市名称'].unique().tolist(),
    *df['城市简称'].unique().tolist(),
  ]
  return [c for c in city_list if not_empty(c)]


def is_city(name):
  """是否是城市"""
  return name in get_city_list()


@lru_cache()
def get_region_list():
  """全部区县（全程+简称）列表"""
  df = get_bd_region()[['区县名称', '区县简称']]
  region_list = [
    *df['区县名称'].unique().tolist(),
    *df['区县简称'].unique().tolist(),
  ]
  return [c for c in region_list if not_empty(c)]


def is_region(name):
  """是否是区县"""
  return name in get_region_list()


@lru_cache()
def city_full_short_mapping():
  """全称和简称的映射关系"""
  df = get_bd_region()[['城市名称', '城市简称']]
  df = df.drop_duplicates(subset=['城市名称']).dropna()
  return df.set_index('城市名称').to_dict()['城市简称']


@lru_cache()
def city_short_full_mapping():
  """简称和全称的映射关系"""
  df = get_bd_region()[['城市名称', '城市简称']]
  df = df.drop_duplicates(subset=['城市简称']).dropna()
  return df.set_index('城市简称').to_dict()['城市名称']


@lru_cache()
def region_full_city_mapping():
  """区县名称和城市简称的映射关系，仅保留一对一的关系"""
  df = get_bd_region()[['区县名称', '城市简称']]
  df = df.drop_duplicates(subset=['区县名称'], keep=False).dropna()
  return df.set_index('区县名称').to_dict()['城市简称']


@lru_cache()
def region_short_city_mapping():
  """区县简称和城市简称的映射关系，仅保留一对一的关系"""
  df = get_bd_region()[['区县简称', '城市简称']]
  df = df.drop_duplicates(subset=['区县简称'], keep=False).dropna()
  return df.set_index('区县简称').to_dict()['城市简称']


@lru_cache()
def city_shortname_id_mapping():
  """城市名称和城市id的映射关系"""
  df = get_bd_region()[['城市简称', '城市id']]
  df = df.drop_duplicates(subset=['城市简称']).dropna()
  return df.set_index('城市简称').to_dict()['城市id']


@lru_cache()
def city_id_shortname_mapping():
  """城市id和城市名称的映射关系"""
  df = get_bd_region()[['城市id', '城市简称']]
  df = df.drop_duplicates(subset=['城市id']).dropna()
  return df.set_index('城市id').to_dict()['城市简称']


@lru_cache()
def norm_city_name(name, full=False, warning=False):
  """标准化城市名称为简称或全称"""
  if not name:
    return
  fs = city_full_short_mapping()
  sf = city_short_full_mapping()
  if full:
    city = name if name in fs else sf.get(name)
  else:
    city = name if name in sf else fs.get(name)
  if not city:
    warn_(f'未找到城市名称：{name}', if_or_not=warning)
  return city


@lru_cache()
def get_city_id_by_name(name: str, warning=True):
  """根据城市名称获取城市id"""
  name = norm_city_name(name, warning=warning)
  shortname_id = city_shortname_id_mapping()
  city_id = shortname_id.get(name)
  if not city_id:
    warn_(f'未找到城市id：{name}', if_or_not=warning)
  return city_id


@lru_cache()
def get_city_name_by_id(city_id: (str, int), full=False, warning=False):
  """根据城市id获取城市名称"""
  if isinstance(city_id, (int, float)):
    city_id = str(int(city_id))
  id_shortname = city_id_shortname_mapping()
  city_name = id_shortname.get(city_id)
  if not city_name:
    warn_(f'未找到城市名称：{city_id}', if_or_not=warning)
  return norm_city_name(city_name, full=full, warning=warning)


@lru_cache()
def ensure_city_name(name, full=False, warning=False):
  """输入城市或区县，返回城市"""
  if not name:
    return
  city = norm_city_name(name, full=full, warning=warning)
  if city:
    return city
  rf_c = region_full_city_mapping()
  rs_c = region_short_city_mapping()
  city = rf_c.get(name) or rs_c.get(name)
  if not city:
    warn_(f'未找到城市名称：{name}', if_or_not=warning)
  return norm_city_name(city, full=full, warning=warning)


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


@check_null(default_rv=[])
def extract_possible_region(string: str) -> list:
  """从字符串中提取可能的城市、区县"""
  if not isinstance(string, str):
    return []
  ls = []
  city_num, region_num = 0, 0
  # 根据正则表达式提取城市和区县
  for pattern in [*AddressPattern.cities, *AddressPattern.regions]:
    if res := re_fast(pattern, string, warning=False):
      if is_city(res):
        ls.append(res)
        city_num += 1
      if is_region(res):
        ls.append(res)
        region_num += 1
  # 没提取出区县时，按照字符串匹配尝试提取
  if region_num == 0:
    for cr in regions():
      if cr in string:
        ls.append(cr)
        break
  # 没提取出城市时，按照字符串匹配尝试提取
  if city_num == 0:
    for cr in cities():
      if cr in string:
        ls.append(cr)
        break
  ls = list(set(ls))
  ls1 = [i for i in ls if i.endswith('市')]
  ls2 = [i for i in ls if not i.endswith('市')]
  return [*ls1, *ls2]


def get_city_and_region(string) -> tuple:
  """从字符串中提取城市、区县"""
  city_list, region_list = [], []
  ls = extract_possible_region(string)
  for i in ls:
    if is_city(i):
      city_list.append(i)
    if is_region(i):
      region_list.append(i)
  if region_list and not city_list:
    for r in region_list:
      if _city := ensure_city_name(r, warning=False):
        city_list.append(_city)
  return (
    city_list[0] if city_list else None,
    region_list[0] if region_list else None,
    city_list,
    region_list
  )


@lru_cache()
def extract_city(string: str, na=None):
  """从字符串中提取城市（可能包含县级市）"""
  res = get_city_and_region(string)
  rv = res[0] or res[1]
  if is_empty(rv):
    return na
  return rv


class District:
  def __init__(self):
    """自动转换行政区划"""
    self.df = get_bd_region()

  @cached_property
  def city_list(self):
    """全部城市（全程+简称）列表"""
    return get_city_list()

  @cached_property
  def region_list(self):
    """全部区县（全程+简称）列表"""
    return get_region_list()

  @staticmethod
  def is_city(name: str) -> bool:
    """判断是否是地级市"""
    return is_city(name)

  @staticmethod
  def is_region(name: str) -> bool:
    """判断是否是县市区"""
    return is_region(name)

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
                    if_not_unique: str = 'coerce',
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
    assert if_not_unique in ['coerce', 'first', 'last', 'all']
    if type_ == 'city':
      ls = self.city_names(name)
    elif type_ == 'province':
      ls = self.province_names(name)
    else:
      raise ValueError('type_ must be "city" or "province"')
    return if_many_value(ls, action=if_not_unique, warning=warning)

  def city(self, name: str,
           if_not_unique: str = 'coerce',
           warning: bool = True):
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

  def province(self, name, if_not_unique='coerce', warning=True):
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

  @staticmethod
  def get_city_id_by_name(name: str, warning=True):
    """通过城市名称获取城市id"""
    return get_city_id_by_name(name, warning=warning)

  @staticmethod
  def get_city_name_by_id(city_id: int, full=False, warning=False):
    """通过城市id获取城市名称"""
    return get_city_name_by_id(city_id, full=full, warning=warning)
