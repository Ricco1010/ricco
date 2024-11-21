import re
import warnings

from ..geometry.coord_trans import _gcj2bd
from ..geometry.coord_trans import _gcj2wgs
from ..util.decorator import check_null

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
  # MC geocode服务
  mdt = 'https://geocode.idatatlas.com/geocode'


class MapKeys:
  amap = '7c14855824549a84c543e48990239f3d'  # noqa
  baidu = '9Fy1lMHbwpr07WVBFPLw9vpntGUSOUMN'  # noqa


def gcj2xx(lnglat, srs):
  assert srs in ('wgs84', 'bd09', 'gcj02'), '可选参数为bd09,wgs84,gcj02'
  if srs == 'wgs84':
    return _gcj2wgs(float(lnglat[1]), float(lnglat[0]))
  elif srs == 'bd09':
    return _gcj2bd(float(lnglat[1]), float(lnglat[0]))
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


@check_null(default_rv='')
def fix_address(string):
  string = str(string)
  string = re.sub(r'[&%#@$|]', '', string)
  string = re.sub(r'(.*?路.*?号).*', r'\1', string)
  string = re.sub('\d+室', '', string)
  string = re.sub('\d+层', '', string)
  return string


@check_null(default_rv='中国')
def fix_city(string):
  return str(string).rstrip('市')


def rv_score(city, address, rv):
  from fuzzywuzzy import fuzz
  if not all([address, rv]):
    return -1
  city = fix_address(city)
  return max(
      fuzz.ratio(rv.lstrip(city), address.lstrip(city)),
      fuzz.partial_ratio(rv.lstrip(city), address.lstrip(city))
  )
