import logging
import uuid
import warnings

import pandas as pd
from requests.exceptions import ConnectionError
from requests.exceptions import ConnectTimeout
from tqdm import tqdm

from ..util.util import is_empty
from .amap import get_address_amap
from .amap import get_place_amap
from .baidu import get_address_baidu
from .baidu import get_place_baidu


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
  if source == 'baidu':
    return get_address_baidu(city=city, address=address, srs=srs, key=key_baidu)
  elif source == 'baidu_poi':
    return get_place_baidu(city=city, keywords=address, srs=srs, key=key_baidu)
  elif source == 'amap':
    return get_address_amap(city=city, address=address, srs=srs, key=key_amap)
  elif source == 'amap_poi':
    return get_place_amap(city=city, keywords=address, srs=srs, key=key_amap)
  else:
    return ValueError('source参数错误')


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
    return None, None, None, None, None
  res = {
    'lng': None,
    'lat': None,
    'rv': None,
    'score': None,
  }
  source = None
  try:
    ar = get_place_amap(city, keywords, srs=srs, key=key_amap)
    if ar['score'] >= 90:
      res, source = ar, 'amap_poi'
    else:
      br = get_place_baidu(city, keywords, srs=srs, key=key_baidu)
      if (br['score'] >= ar['score']) and (br['score'] >= sig):
        res, source = br, 'baidu_poi'
      elif (ar['score'] >= br['score']) and (ar['score'] >= sig):
        res, source = ar, 'amap_poi'
      elif address_geocode:
        br = get_address_baidu(city, keywords, srs=srs, key=key_baidu)
        if br['score'] >= 90:
          res, source = br, 'baidu_geocode'
        else:
          ar = get_address_amap(city, keywords, srs=srs, key=key_amap)
          res, source = ar, 'amap_geocode'
    return res['lng'], res['lat'], res['rv'], res['score'], source

  except (ConnectionError, ConnectTimeout, TimeoutError) as e:
    warnings.warn(f'接口超时，【{city}】：【{keywords}】,{e}')
    return None, None, None, None, None


def geocode_best_address(city, address, srs='wgs84', key_baidu=None,
                         key_amap=None):
  """获取最优的地理编码结果"""
  if is_empty(address):
    return None, None, None, None, None
  try:
    br = get_address_baidu(city, address, srs=srs, key=key_baidu)
    if br['score'] >= 90:
      res, source = br, 'baidu_geocode'
    else:
      ar = get_address_amap(city, address, srs=srs, key=key_amap)
      res, source = ar, 'amap_geocode'
    return res['lng'], res['lat'], res['rv'], res['score'], source

  except (ConnectionError, ConnectTimeout, TimeoutError) as e:
    warnings.warn(f'接口超时，【{city}】：【{address}】,{e}')
    return None, None, None, None, None


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
  temp_city_col = uuid.uuid1()

  if isinstance(city, str):
    df[temp_city_col] = city
  elif isinstance(city, list):
    df[temp_city_col] = df[city]
  else:
    raise TypeError(f'city类型错误，请传入list或str类型')

  on = [temp_city_col, by]
  df_temp = df[on].drop_duplicates().reset_index(drop=True)

  for i in tqdm(df_temp.index):
    try:
      kw = df_temp[by][i]
      ct = df_temp[temp_city_col][i]
      if address_type == 'poi':
        rv = geocode_best_poi(
            ct, kw,
            sig=sig,
            address_geocode=address_geocode,
            srs=srs,
            key_baidu=key_baidu,
            key_amap=key_amap)
      elif address_type == 'address':
        rv = geocode_best_address(ct, kw, srs=srs,
                                  key_baidu=key_baidu, key_amap=key_amap)
      else:
        raise ValueError('参数address_type错误，可选参数为"poi"或"address"')
      df_temp.loc[
        (df_temp[temp_city_col] == ct) & (df_temp[by] == kw),
        ['lng', 'lat', 'rv', 'geocode_score', 'geocode_type']] = rv
    except Exception as e:
      logging.warning(f'{e},{kw}')

  df = df.merge(df_temp, on=on, how='left')
  if not with_detail:
    del df['rv'], df['geocode_score'], df['geocode_type']
  del df[temp_city_col]
  return df
