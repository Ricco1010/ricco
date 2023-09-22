import logging
import uuid
import warnings

import pandas as pd
from tqdm import tqdm

from ..etl.transformer import create_columns
from ..util.util import is_empty
from .amap import get_address_amap
from .amap import get_place_amap
from .baidu import get_address_baidu
from .baidu import get_place_baidu
from .util import DEFAULT_RES


def geocode(*,
            address,
            city,
            source,
            srs='wgs84',
            key_baidu=None,
            key_amap=None):
  """
  Args:
    address: 地址或项目名称关键词
    city: 城市
    source: 接口选择。baidu/amap：百度或高德的地理编码接口，baidu_poi/amap_poi：百度或高德的地点检索接口
    srs: 返回的坐标系，可选wgs84, bd09, gcj02，默认wgs84
    key_baidu: 百度接口的key，公共key失效后可自行传入
    key_amap: 高德接口的key，公共key失效后可自行传入
  """
  assert source in ('baidu', 'baidu_poi', 'amap', 'amap_poi')
  if source == 'baidu':
    return get_address_baidu(city=city, address=address, srs=srs, key=key_baidu)
  if source == 'baidu_poi':
    return get_place_baidu(city=city, keywords=address, srs=srs, key=key_baidu)
  if source == 'amap':
    return get_address_amap(city=city, address=address, srs=srs, key=key_amap)
  if source == 'amap_poi':
    return get_place_amap(city=city, keywords=address, srs=srs, key=key_amap)


def geocode_best_poi(city,
                     keywords,
                     sig=80,
                     address_geocode=False,
                     srs='wgs84',
                     key_baidu=None,
                     key_amap=None):
  """
  获取最优的地点检索结果
  Args:
    city: 城市
    keywords: POI名称
    sig: 解析结果相似度，默认为80，范围0-100
    address_geocode: 是否使用地理编码补全，默认False
    srs: 返回的坐标系，可选wgs84, bd09, gcj02，默认wgs84
    key_baidu: 百度接口的key，公共key失效后可自行传入
    key_amap: 高德接口的key，公共key失效后可自行传入
  """
  if is_empty(keywords):
    return DEFAULT_RES
  try:
    ar = get_place_amap(city, keywords, srs=srs, key=key_amap)
    if ar['score'] >= 90:
      return ar
    br = get_place_baidu(city, keywords, srs=srs, key=key_baidu)
    if br['score'] >= sig or ar['score'] >= sig:
      return br if br['score'] > ar['score'] else ar
    if address_geocode:
      br = get_address_baidu(city, keywords, srs=srs, key=key_baidu)
      if br['score'] >= 90:
        return br
      return get_address_amap(city, keywords, srs=srs, key=key_amap)
  except Exception as e:
    warnings.warn(f'结果获取失败：【{city}】：【{keywords}】,{e}')
    return DEFAULT_RES


def geocode_best_address(city, address, srs='wgs84', key_baidu=None,
                         key_amap=None):
  """获取最优的地理编码结果"""
  if is_empty(address):
    return DEFAULT_RES
  try:
    br = get_address_baidu(city, address, srs=srs, key=key_baidu)
    if br['score'] >= 90:
      return br
    return get_address_amap(city, address, srs=srs, key=key_amap)
  except Exception as e:
    warnings.warn(f'结果获取失败：【{city}】：【{address}】,{e}')
    return DEFAULT_RES


def geocode_best(city, address,
                 address_type: str,
                 sig: int = 80,
                 srs: str = 'wgs84',
                 address_geocode: bool = False,
                 key_baidu=None, key_amap=None):
  assert address_type in ('poi', 'address'), 'address_type可选参数为poi或address'
  if address_type == 'poi':
    return geocode_best_poi(
        city, address, sig=sig, address_geocode=address_geocode, srs=srs,
        key_baidu=key_baidu, key_amap=key_amap
    )
  return geocode_best_address(
      city, address, srs=srs, key_baidu=key_baidu, key_amap=key_amap
  )


def geocode_with_memory_cache(
    city, address, address_type: str,
    sig: int = 80, srs: str = 'wgs84',
    address_geocode: bool = False,
    key_baidu=None, key_amap=None,
    ignore_existing=True, lng=None, lat=None, memory_cache: bool = True):
  """geocoding（使用内存加速）"""
  if not all([city, address]):
    return DEFAULT_RES
  if memory_cache:
    global __GLOBAL_CACHE
    if '__GLOBAL_CACHE' not in globals():
      __GLOBAL_CACHE = {}
    if city in __GLOBAL_CACHE:
      if address in __GLOBAL_CACHE[city]:
        return __GLOBAL_CACHE[city][address]

  if ignore_existing and all([lng, lat]):
    rv = DEFAULT_RES.copy()
    rv['lng'] = lng
    rv['lat'] = lat
    return rv
  res = geocode_best(
      city=city, address=address, sig=sig,
      address_type=address_type, address_geocode=address_geocode,
      srs=srs, key_baidu=key_baidu, key_amap=key_amap
  )
  if memory_cache:
    if city not in __GLOBAL_CACHE:
      __GLOBAL_CACHE[city] = {}
    __GLOBAL_CACHE[city][address] = res
  return res


def geocode_df(df: pd.DataFrame,
               by: str,
               city: (str, list),
               address_type: str,
               sig: int = 80,
               address_geocode: bool = False,
               with_detail: bool = True,
               srs: str = 'wgs84',
               key_baidu=None,
               key_amap=None):
  """
  对dataframe进行geocoding
  Args:
    df:
    by: 项目名称所在的列
    city: 城市，list表示城市列如['城市']， str表示全部使用该城市如'上海'
    address_type: 'poi'或'address'，不同的地理类型对应不同的接口，精确度不同
    sig: 解析结果相似度，默认为80，范围为0-100，仅当address_type为poi时生效
    address_geocode: poi解析时是否使用地理编码补全，默认False，仅当address_type为poi时生效
    with_detail: 是否返回详情信息，包括返回值、得分、接口来源等
    srs: 返回的坐标系，可选wgs84, bd09, gcj02，默认wgs84
    key_baidu: 百度接口的key，公共key失效后可自行传入
    key_amap: 高德接口的key，公共key失效后可自行传入
  """
  assert address_type in ('poi', 'address'), 'address_type可选参数为poi或address'
  assert isinstance(city, (str, list))
  assert 'lng' not in df, '原数据中不能有lng列'
  assert 'lat' not in df, '原数据中不能有lat列'

  __c_city = uuid.uuid1()
  on = [__c_city, by]

  df[__c_city] = city if isinstance(city, str) else df[city]

  _df = df[on].drop_duplicates().reset_index(drop=True)
  base_cols = ['lng', 'lat']
  if with_detail:
    base_cols.extend(['rv', 'score', 'source'])
  _df = create_columns(_df, base_cols)
  for i in tqdm(_df.index):
    _address = None
    try:
      _address, _city = _df[by][i], _df[__c_city][i]
      rv = geocode_best(
          city=_city, address=_address, sig=sig,
          address_type=address_type, address_geocode=address_geocode,
          srs=srs, key_baidu=key_baidu, key_amap=key_amap
      )
      for c in base_cols:
        _df.loc[(_df[__c_city] == _city) & (_df[by] == _address), c] = rv[c]
    except Exception as e:
      logging.warning(f'{e},{_address}')
  df = df.merge(_df, on=on, how='left')
  del df[__c_city]
  return df


def geocode_v2(df: pd.DataFrame,
               by: str,
               city: (str, list),
               address_type: str,
               sig: int = 80,
               address_geocode: bool = False,
               with_detail: bool = True,
               srs: str = 'wgs84',
               ignore_existing: bool = True,
               key_baidu=None,
               key_amap=None,
               memory_cache: bool = True):
  """
  对dataframe进行geocoding
  Args:
    df:
    by: 项目名称所在的列
    city: 城市，list表示城市列如['城市']， str表示全部使用该城市如'上海'
    address_type: 'poi'或'address'，不同的地理类型对应不同的接口，精确度不同
    sig: 解析结果相似度，默认为80，范围为0-100，仅当address_type为poi时生效
    address_geocode: poi解析时是否使用地理编码补全，默认False，仅当address_type为poi时生效
    with_detail: 是否返回详情信息，包括返回值、得分、接口来源等
    srs: 返回的坐标系，可选wgs84, bd09, gcj02，默认wgs84
    ignore_existing: 是否忽略已有的经纬度，默认True
    key_baidu: 百度接口的key，公共key失效后可自行传入
    key_amap: 高德接口的key，公共key失效后可自行传入
    memory_cache: 是否使用内存缓存，默认True
  """
  assert address_type in ('poi', 'address'), 'address_type可选参数为poi或address'
  assert isinstance(city, (str, list))
  assert df.index.is_unique, 'DataFrame索引列必须唯一'

  __c_city = uuid.uuid1()
  df[__c_city] = city if isinstance(city, str) else df[city]

  base_cols = ['lng', 'lat']
  if with_detail:
    base_cols.extend(['rv', 'score', 'source'])
  df = create_columns(df, base_cols)

  for i in tqdm(df.index):
    _address, _city = df[by][i], df[__c_city][i]
    _lng, _lat = df['lng'][i], df['lat'][i]
    try:
      rv = geocode_with_memory_cache(
          city=_city, address=_address, sig=sig,
          address_type=address_type, address_geocode=address_geocode,
          srs=srs, key_baidu=key_baidu, key_amap=key_amap,
          ignore_existing=ignore_existing, lng=_lng, lat=_lat,
          memory_cache=memory_cache,
      )
      for c in base_cols:
        df.loc[(df[__c_city] == _city) & (df[by] == _address), c] = rv[c]
    except Exception as e:
      logging.warning(f'{e},{_address}')
  del df[__c_city]
  return df
