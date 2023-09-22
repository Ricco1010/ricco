import warnings

from ..geometry.coord_trans import gcj2bd
from ..geometry.coord_trans import gcj2wgs
from ..geometry.util import is_empty

DEFAULT_RES = {
  'rv': None, 'score': -1,
  'lng': None, 'lat': None,
  'source': None
}


class MapUrls:
  # 百度地理编码
  baidu = 'http://api.map.baidu.com/geocoding/v3/'
  # 百度地点检索
  baidu_poi = 'http://api.map.baidu.com/place/v2/search'
  # 高德地理编码
  amap = 'https://restapi.amap.com/v3/geocode/geo'
  # 高德地点检索
  amap_poi = 'https://restapi.amap.com/v3/place/text'
  # 脉策geocode服务
  mdt = 'https://geocode.idatatlas.com/geocode'


class MapKeys:
  amap = '7c14855824549a84c543e48990239f3d'
  baidu = '9Fy1lMHbwpr07WVBFPLw9vpntGUSOUMN'


def gcj2xx(lnglat, srs):
  assert srs in ('wgs84', 'bd09', 'gcj02'), '可选参数为bd09,wgs84,gcj02'
  if srs == 'wgs84':
    return gcj2wgs(float(lnglat[1]), float(lnglat[0]))
  elif srs == 'bd09':
    return gcj2bd(float(lnglat[1]), float(lnglat[0]))
  else:
    return float(lnglat[1]), float(lnglat[0])


def error_baidu(js):
  if js['status'] != 0:
    warnings.warn(
        f'接口错误，状态码【{js["status"]}】，错误原因请查阅：https://lbsyun.baidu.com/index.php?title=webapi/appendix')


def error_amap(js):
  if js['status'] != '1':
    warnings.warn(
        f'接口错误，状态码【{js["infocode"]}】，错误原因请查阅：https://lbs.amap.com/api/webservice/guide/tools/info')


def fix_address(string):
  if is_empty(string):
    return ''
  string = str(string)
  for _ in ['&', '%', '#', '@', '$', '|']:
    string = string.replace(_, '')
  return string


def fix_city(string):
  if is_empty(string):
    return '中国'
  return str(string).rstrip('市')


def rv_score(city, keywords, rv):
  from fuzzywuzzy import fuzz
  if not all([keywords, rv]):
    return -1
  city = fix_address(city)
  return max(
      fuzz.ratio(rv.lstrip(city), keywords.lstrip(city)),
      fuzz.partial_ratio(rv.lstrip(city), keywords.lstrip(city))
  )
