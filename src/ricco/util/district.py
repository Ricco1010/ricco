from functools import cached_property
from functools import lru_cache

import ahocorasick

from ..base import ensure_list
from ..base import is_empty
from ..base import warn_
from ..resource.bd_region import cities_all
from ..resource.bd_region import get_bd_region
from ..resource.bd_region import regions_all
from ..resource.patterns import city_region_compiles
from .util import re_multi


def build_automaton(ls):
  """构建前缀树"""
  automaton = ahocorasick.Automaton()
  for idx, values in enumerate(ls):
    automaton.add_word(values, (idx, values))
  automaton.make_automaton()
  return automaton


@lru_cache()
def build_city():
  kwds = cities_all()
  return build_automaton(kwds)


@lru_cache()
def build_region():
  kwds = regions_all()
  return build_automaton(kwds)


def find_cities(text):
  """从字符串中获取全部的城市名称的简称列表"""
  if not isinstance(text, str):
    return []
  automaton = build_city()
  results = set()
  for end_index, (idx, value) in automaton.iter_long(text):
    results.add(value)
  return sorted(list(results), key=lambda x: len(x), reverse=True)


def find_regions(text):
  """从字符串中获取全部的区县名称的简称列表"""
  if not isinstance(text, str):
    return []
  automaton = build_region()
  results = set()
  for end_index, (idx, value) in automaton.iter_long(text):
    results.add(value)
  return sorted(list(results), key=lambda x: len(x), reverse=True)


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


def is_city(name):
  """是否是城市"""
  return name in cities_all()


def is_region(name):
  """是否是区县"""
  return name in regions_all()


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
  if city := norm_city_name(name, full=full, warning=warning):
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


@lru_cache()
def get_city_and_region(string) -> tuple:
  """从字符串中提取城市、区县"""

  def make_shi_behind(_city_list):
    ls1 = [i for i in _city_list if i.endswith('市')]
    ls2 = [i for i in _city_list if not i.endswith('市')]
    return [*ls1, *ls2]

  if not isinstance(string, str):
    return (None, None, [], [])
  ls = re_multi(city_region_compiles(), string)

  city_list = [i for i in ls if is_city(i)]
  if not city_list:
    # 没提取出城市时，按照字符串匹配尝试提取
    city_list.extend(find_cities(string))
  city_list = make_shi_behind(city_list)

  region_list = [i for i in ls if is_region(i)]
  if not region_list:
    # 没提取出区县时，按照字符串匹配尝试提取
    region_list.extend(find_regions(string))

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
    return cities_all()

  @cached_property
  def region_list(self):
    """全部区县（全程+简称）列表"""
    return regions_all()

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
