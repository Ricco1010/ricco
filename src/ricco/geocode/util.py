import warnings

from ..util.coord_trans import gcj2bd
from ..util.coord_trans import gcj2wgs
from ..util.util import is_empty


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
  if srs == 'wgs84':
    return gcj2wgs(float(lnglat[1]), float(lnglat[0]))
  elif srs == 'bd09':
    return gcj2bd(float(lnglat[1]), float(lnglat[0]))
  elif srs == 'gcj02':
    return float(lnglat[1]), float(lnglat[0])
  else:
    raise ValueError('参数输入错误，可选参数为bd09,wgs84,gcj02')


def error_baidu(js):
  if js['status'] != 0:
    warnings.warn(
        '接口错误，状态码【%s】，错误原因请查阅：'
        'https://lbsyun.baidu.com/index.php?title=webapi/appendix' % js[
          'status']
    )


def error_amap(js):
  if js['status'] != '1':
    warnings.warn(
        '接口错误，状态码【%s】，错误原因请查阅：'
        'https://lbs.amap.com/api/webservice/guide/tools/info' % js['infocode']
    )


def fix_address(string):
  if is_empty(string):
    return ''
  return str(string)


def rv_score(city, keywords, rv):
  from fuzzywuzzy import fuzz
  return max(
      fuzz.ratio(rv, keywords.lstrip(city)),
      fuzz.partial_ratio(rv, keywords.lstrip(city))
  )
