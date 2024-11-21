import logging
import uuid
import warnings
from functools import lru_cache

import pandas as pd
from tqdm import tqdm

from ..base import not_empty
from ..etl.transformer import create_columns
from ..util.decorator import check_null
from .amap import get_address_amap
from .amap import get_place_amap
from .baidu import get_address_baidu
from .baidu import get_place_baidu
from .util import DEFAULT_RES


@lru_cache(maxsize=1024)
def geocode(*,
            address,
            city,
            source,
            srs='wgs84',
            key_baidu=None,
            key_amap=None):
  """
  对单个地址进行地理编码的方法汇总，返回经纬度坐标，可通过参数选择geocoding方法

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
    return get_address_baidu(address=address, city=city, srs=srs, key=key_baidu)
  if source == 'baidu_poi':
    return get_place_baidu(address=address, city=city, srs=srs, key=key_baidu)
  if source == 'amap':
    return get_address_amap(address=address, city=city, srs=srs, key=key_amap)
  if source == 'amap_poi':
    return get_place_amap(address=address, city=city, srs=srs, key=key_amap)


@check_null(default_rv=DEFAULT_RES)
def geocode_best_poi(
    address,
    city,
    sig=80,
    address_geocode=False,
    srs='wgs84',
    key_baidu=None,
    key_amap=None):
  """
  获取最优的地点检索结果

  Args:
    address: POI名称
    city: 城市
    sig: 解析结果相似度，默认为80，范围0-100
    address_geocode: 是否使用地理编码补全，默认False
    srs: 返回的坐标系，可选wgs84, bd09, gcj02，默认wgs84
    key_baidu: 百度接口的key，公共key失效后可自行传入
    key_amap: 高德接口的key，公共key失效后可自行传入
  """
  try:
    ar = get_place_amap(address, city, srs=srs, key=key_amap)
    if ar['score'] >= 90:
      return ar
    br = get_place_baidu(address, city, srs=srs, key=key_baidu)
    if br['score'] >= sig or ar['score'] >= sig:
      return br if br['score'] > ar['score'] else ar
    if address_geocode:
      br = get_address_baidu(address, city, srs=srs, key=key_baidu)
      if br['score'] >= 90:
        return br
      return get_address_amap(address, city, srs=srs, key=key_amap)
  except Exception as e:
    warnings.warn(f'结果获取失败：【{city}】：【{address}】,{e}')
  return DEFAULT_RES


@check_null(default_rv=DEFAULT_RES)
def geocode_best_address(address, city, srs='wgs84', key_baidu=None,
                         key_amap=None):
  """获取最优的地理编码结果"""
  try:
    br = get_address_baidu(address, city, srs=srs, key=key_baidu)
    if br['score'] >= 90:
      return br
    return get_address_amap(address, city, srs=srs, key=key_amap)
  except Exception as e:
    warnings.warn(f'结果获取失败：【{city}】：【{address}】,{e}')
  return DEFAULT_RES


@lru_cache(maxsize=1024)
def geocode_best(
    address,
    city,
    address_type: str,
    sig: int = 80,
    srs: str = 'wgs84',
    address_geocode: bool = False,
    **kwargs):
  """
  获取最优的geocoding结果

  Args:
    address: 地址
    city: 城市
    address_type: 'poi' 或 'address'，不同的地理类型对应不同的接口，精确度不同
    sig: 得分
    srs: 坐标系
    address_geocode: 是否使用地址编码进行补充
    **kwargs:
  """
  assert address_type in ('poi', 'address'), 'address_type可选参数为poi或address'
  if address_type == 'poi':
    return geocode_best_poi(
        address, city, sig=sig, address_geocode=address_geocode, srs=srs,
        **kwargs
    )
  return geocode_best_address(address, city, srs=srs, **kwargs)


def geocode_df(df: pd.DataFrame,
               by: str,
               city: (str, list),
               address_type: str,
               sig: int = 80,
               address_geocode: bool = False,
               with_detail: bool = True,
               srs: str = 'wgs84',
               c_lng='lng',
               c_lat='lat',
               ignore_existing: bool = True,
               progress_bar: bool = True,
               **kwargs):
  """
  基于dataframe进行geocoding

  Args:
    df: 数据集
    by: 地址或名称列
    city: 城市，如为list表示城市列，如['城市']；如为str表示全部使用该城市,如 "上海"
    address_type: 'poi' 或 'address'，不同的地理类型对应不同的接口，精确度不同
    sig: 解析结果相似度，默认为80，范围为0-100，仅当address_type为poi时生效
    address_geocode: poi解析时是否使用地理编码补全，默认False，仅当address_type为poi时生效
    with_detail: 是否返回详情信息，包括返回值、得分、接口来源等
    srs: 返回的坐标系，可选wgs84, bd09, gcj02，默认wgs84
    c_lng: 经度列名，默认为 'lng'
    c_lat: 纬度列名，默认为 'lat'
    ignore_existing: 是否忽略已经存在经纬的行，默认为 TRUE，即保持原有的经纬度不变
    key_baidu: 百度接口的key，公共key失效后可自行传入
    key_amap: 高德接口的key，公共key失效后可自行传入
    progress_bar: 是否显示进度条，默认为TRUE

  See Also:
    * :func:`ricco.geocode.geocode.geocode_best`
  """
  assert address_type in ('poi', 'address'), 'address_type可选参数为poi或address'
  assert isinstance(city, (str, list)), 'city参数类型应为 str 或 list'
  assert df.index.is_unique, 'df的index必须唯一'

  __c_city = f'city-{uuid.uuid1()}'
  # 最后要输出的列
  base_cols = [c_lng, c_lat]
  if with_detail:
    base_cols.extend(['rv', 'score', 'source'])
  # 补全列，方便后续进行update
  df = create_columns(df.copy(), base_cols)
  num_all = df[df[c_lng].isna()].shape[0]
  # 新增临时城市列
  df[__c_city] = city if isinstance(city, str) else df[city[0]]

  indexes = []
  datas = []
  for _data in tqdm(
      df[[__c_city, by, c_lng, c_lat]].itertuples(),
      desc='Geocoding', total=df.shape[0], disable=not progress_bar
  ):
    if ignore_existing and not_empty(_data[3]) and not_empty(_data[4]):
      # ignore_existing为TRUE时，已经存在经纬度的行不再进行geocoding
      continue
    rv = geocode_best(
        address=_data[2], city=_data[1], sig=sig,
        address_type=address_type, address_geocode=address_geocode,
        srs=srs, **kwargs
    )
    rv[c_lng] = rv['lng']
    rv[c_lat] = rv['lat']
    datas.append(rv)
    indexes.append(_data[0])
  df_temp = pd.DataFrame(datas, index=indexes)
  df.update(df_temp[base_cols])
  num_miss = df[df[c_lng].isna()].shape[0]
  logging.warning(f'总数：{num_all}，成功：{num_all - num_miss}，失败：{num_miss}')
  # 删除临时城市列
  del df[__c_city]
  return df
