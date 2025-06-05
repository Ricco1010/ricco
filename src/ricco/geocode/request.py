import requests

from ..util.decorator import check_null
from .util import MapKeys
from .util import MapUrls


@check_null()
def request_amap_addr(address, city, key=None):
  """高德地图-地理编码"""
  if key is None:
    key = MapKeys.amap
  url = f'{MapUrls.amap}?address={address}&city={city}&key={key}'
  js = requests.get(url).json()
  # 超过并发限制的重新请求
  if js['status'] == '0' and js['infocode'] == '10021':
    return request_amap_addr(address, city, key)
  return js


@check_null()
def request_amap_place(address, city, key=None):
  """高德地图-地点检索"""
  if key is None:
    key = MapKeys.amap
  url = f'{MapUrls.amap_poi}?keywords={address}&city={city}&key={key}'
  js = requests.get(url).json()
  # 超过并发限制的重新请求
  if js['status'] == '0' and js['infocode'] == '10021':
    return request_amap_place(address, city, key)
  return js


@check_null()
def request_baidu_addr(address, city, key=None):
  """百度地图-地理编码"""
  if key is None:
    key = MapKeys.baidu
  url = f'{MapUrls.baidu}?city={city}&address={address}&output=json&ak={key}&ret_coordtype=gcj02ll'
  js = requests.get(url).json()
  # 超过并发限制的重新请求
  if js['status'] == 401:
    return request_baidu_addr(address, city, key)
  return js


@check_null()
def request_baidu_place(address, city, key=None):
  """百度地图-地点检索"""
  if key is None:
    key = MapKeys.baidu
  url = f'{MapUrls.baidu_poi}?query={address}&region={city}&city_limit=true&output=json&ak={key}&ret_coordtype=gcj02ll'
  js = requests.get(url).json()
  # 超过并发限制的重新请求
  if js['status'] == 401:
    return request_baidu_place(address, city, key)
  return js


@check_null()
def request_mdt(
    address,
    city,
    source,
    disable_cache=False,
    with_detail=True,
    key=None):
  url = f'{MapUrls.mdt}?address={address}&city={city}&disable_cache={disable_cache}&with_detail={with_detail}&source={source}'
  if key:
    url += f'&key={key}'
  return requests.get(url)


def func_call(source):
  """根据source返回对应的函数"""
  assert source in [
    'baidu', 'amap', 'baidu_poi', 'amap_poi'
  ], 'source must be baidu/amap/baidu_poi/amap_poi'
  if source == 'baidu':
    return request_baidu_addr
  if source == 'amap':
    return request_amap_addr
  if source == 'baidu_poi':
    return request_baidu_place
  if source == 'amap_poi':
    return request_amap_place
