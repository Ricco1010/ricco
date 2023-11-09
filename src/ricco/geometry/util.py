import json
import re
import sys
import warnings
from typing import List

import geojson
import numpy as np
import pandas as pd
from shapely import wkb
from shapely import wkt
from shapely.errors import GeometryTypeError
from shapely.errors import WKBReadingError
from shapely.geometry import MultiLineString
from shapely.geometry import MultiPolygon
from shapely.geometry import Point
from shapely.geometry import Polygon
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.geos import WKTReadingError

from ..util.base import ensure_list
from ..util.base import is_empty
from ..util.base import not_empty
from ..util.decorator import check_null
from ..util.decorator import check_shapely
from ..util.decorator import check_str
from ..util.util import is_hex
from ..util.util import isinstance_in_list


class GeomFormat:
  wkb = 'wkb'
  wkt = 'wkt'
  shapely = 'shapely'
  geojson = 'geojson'
  unknown = 'unknown'


def crs_sh2000():
  """测绘院（上海2000）crs信息"""
  from ..resource.crs import CRS_SH2000
  return CRS_SH2000


def epsg_from_lnglat(lng, lat=0):
  """根据经纬度确定EPSG代码"""
  # 计算 UTM 区域代码
  lng = ensure_list(lng)
  lng = [i for i in lng if not_empty(i)]
  lng = np.median(lng)
  utm_band = str(int((np.floor((lng + 180) / 6) % 60) + 1)).zfill(2)
  return int(f'326{utm_band}' if lat >= 0 else f'327{utm_band}')


def lng_from_city(city: str):
  """获取城市所在的经度"""
  from ..resource.epsg_code import CITY_POINT
  assert len(city) >= 2, '城市名称过短'
  if city in CITY_POINT:
    return CITY_POINT[city]['lng']
  else:
    for _c in CITY_POINT.keys():
      if city in _c:
        return CITY_POINT[_c]['lng']
  warnings.warn(f'请补充"{city}"的epsg信息，默认返回经度113.0')
  return 113.0


def get_epsg(city: str):
  """根据城市查询epsg代码，用于投影"""
  return epsg_from_lnglat(lng_from_city(city))


def projection_lnglat(lnglat, crs_from, crs_to):
  """对经纬度进行投影"""
  from pyproj import Transformer
  transformer = Transformer.from_crs(crs_from, crs_to)
  return transformer.transform(xx=lnglat[1], yy=lnglat[0])


@check_str
def wkb_loads(x: str, hex=True):
  try:
    return wkb.loads(x, hex=hex)
  except (AttributeError, WKBReadingError) as e:
    warnings.warn(f'{e}, 【{x}】')


@check_shapely
def wkb_dumps(x: BaseGeometry, hex=True, srid=4326):
  try:
    return wkb.dumps(x, hex=hex, srid=srid)
  except AttributeError as e:
    warnings.warn(f'{e}, 【{x}】')


@check_str
def wkt_loads(x: str):
  try:
    return wkt.loads(x)
  except (AttributeError, WKTReadingError, TypeError) as e:
    warnings.warn(f'{e}, 【{x}】')


@check_shapely
def wkt_dumps(x: BaseGeometry):
  try:
    return wkt.dumps(x)
  except AttributeError as e:
    warnings.warn(f'{e}, 【{x}】')


@check_null()
def geojson_loads(x: (str, dict)):
  """geojson文本形式转为shapely格式"""
  from simplejson.errors import JSONDecodeError
  if not isinstance(x, (str, dict)):
    warnings.warn(f'TypeError:【{x}】')
    return
  try:
    geom = shape(geojson.loads(x)) if isinstance(x, str) else shape(x)
    if geom.is_empty:
      return
    return geom
  except (JSONDecodeError, AttributeError, GeometryTypeError, ValueError) as e:
    warnings.warn(f'{e}, 【{x}】')


@check_shapely
def geojson_dumps(x: BaseGeometry):
  """shapely转为geojson文本格式"""
  try:
    geom = geojson.Feature(geometry=x)
    return json.dumps(geom.geometry)
  except TypeError as e:
    warnings.warn(f'{e}, 【{x}】')


def is_shapely(x, na=False) -> bool:
  """判断是否为shapely格式"""
  if is_empty(x):
    return na
  if isinstance(x, BaseGeometry):
    return True
  return False


def is_wkb(x, na=False) -> bool:
  """判断是否为wkb格式"""
  if is_empty(x):
    return na
  if not isinstance(x, str) or not is_hex(x):
    return False
  try:
    wkb.loads(x, hex=True)
    return True
  except WKBReadingError:
    return False


def is_wkt(x, na=False) -> bool:
  """判断是否为wkt格式"""
  if is_empty(x):
    return na
  if not isinstance(x, str) or not re.match('^[MPL]', x.lstrip(' (')):
    return False
  try:
    wkt.loads(x)
    return True
  except WKTReadingError:
    return False


def is_geojson(x, na=False) -> bool:
  """判断是否为geojson格式"""
  from simplejson.errors import JSONDecodeError

  if is_empty(x):
    return na
  if not isinstance(x, (str, dict)):
    return False
  try:
    geom = shape(geojson.loads(x)) if isinstance(x, str) else shape(x)
    if geom.is_empty:
      return False
    return True
  except (JSONDecodeError, AttributeError, GeometryTypeError, TypeError):
    return False


def _infer_geom_format(x):
  """推断geometry格式"""
  if is_shapely(x):
    return GeomFormat.shapely
  if is_wkb(x):
    return GeomFormat.wkb
  if is_wkt(x):
    return GeomFormat.wkt
  if is_geojson(x):
    return GeomFormat.geojson
  return GeomFormat.unknown


def infer_geom_format(series: (str, list, tuple, pd.Series, BaseGeometry)):
  """推断geometry格式"""
  if is_empty(series):
    return GeomFormat.unknown
  assert isinstance(series, (str, list, tuple, pd.Series, BaseGeometry))
  if isinstance(series, (list, tuple, pd.Series)):
    for i in series:
      if not_empty(i):
        return _infer_geom_format(i)
  return _infer_geom_format(series)


def ensure_multi_geom(geom):
  """将LineString和Polygon转为multi格式"""
  if geom.geom_type == 'LineString':
    return MultiLineString([geom])
  if geom.geom_type == 'Polygon':
    return MultiPolygon([geom])
  return geom


def multiline2multipolygon(multiline_shapely: MultiLineString, force=False):
  """multiline转为multipolygon，直接首尾相连"""
  coords = []
  for line in multiline_shapely.geoms:
    lngs, lats = line.xy
    for i in range(len(lngs)):
      lng, lat = lngs[i], lats[i]
      point = Point((lng, lat))
      if coords and point == coords[-1]:
        continue
      coords.append(point)
  if len(coords) <= 2:
    return
  if not force and coords[0].distance(coords[-1]) >= 0.000001:
    return
  try:
    return MultiPolygon([Polygon(coords)])
  except Exception as e:
    warnings.warn(f'{e}，{multiline_shapely}')
    return


def get_inner_point(polygon: Polygon, within=True):
  """返回面内的一个点，默认返回中心点，当中心点不在面内则返回面内一个点"""
  if is_empty(polygon):
    return
  point = polygon.centroid
  if not polygon.is_valid:
    polygon = polygon.buffer(0.000001)
  if polygon.contains(point) or not within:
    return point
  return polygon.representative_point()


def is_valid_lnglat(lng, lat):
  """判断经纬度是否有效"""
  return -180 <= lng <= 180 and -90 <= lat <= 90


def auto_loads(x) -> BaseGeometry:
  """自动识别地理格式并转换为shapely格式"""
  geom_format = infer_geom_format(x)
  assert geom_format != GeomFormat.unknown, '未知的地理格式'
  if geom_format == 'shapely':
    return x
  return getattr(sys.modules[__name__], f'{geom_format}_loads')(x)


def dumps2x(x: BaseGeometry, geom_format):
  """转换geometry格式"""
  assert geom_format in ('wkb', 'wkt', 'shapely', 'geojson'), '未知的地理格式'
  x = auto_loads(x)
  if geom_format == 'shapely':
    return x
  return getattr(sys.modules[__name__], f'{geom_format}_dumps')(x)


def ensure_lnglat(lnglat) -> tuple:
  if is_empty(lnglat):
    return np.nan, np.nan
  if isinstance(lnglat, (list, tuple)):
    assert isinstance_in_list(lnglat, (float, int)), '数据类型错误，经度和纬度都应该为数值型'
    assert is_valid_lnglat(*lnglat), '经纬度超出范围'
    return tuple(lnglat)
  if geom := auto_loads(lnglat):
    return geom.centroid.x, geom.centroid.y
  raise ValueError('未知的地理类型')


def distance(
    p1: (tuple, str),
    p2: (tuple, str),
    city: str = None,
    epsg_from: int = 4326,
    epsg_to: (str, int) = None):
  """
  计算两个点（经度，纬度）之间的距离，单位：米
  Args:
    p1: 点位1，经纬度或geometry
    p2: 点位2，经纬度或geometry
    city: 所在城市，用于投影
    epsg_from: epsg代码
    epsg_to: 投影epsg代码
  """
  p1, p2 = ensure_lnglat(p1), ensure_lnglat(p2)
  if not epsg_to:
    epsg_to = get_epsg(city) if city else epsg_from_lnglat([p1[0], p2[0]])
  p1 = projection_lnglat(p1, epsg_from, epsg_to)
  p2 = projection_lnglat(p2, epsg_from, epsg_to)
  return Point(p1).distance(Point(p2))


def get_geoms(geo: BaseGeometry) -> List:
  """
  将geo中包含的LineString、Point、Polygon取出存放到list中
  Args:
    geo: geometry类型的数据

  Returns:
    List：geo中包含的LineString、Point、Polygon
  """
  list_geo = []
  if geo.is_empty:
    list_geo.append(geo)
  elif hasattr(geo, 'geoms'):
    for g in geo.geoms:
      list_geo.extend(get_geoms(g))
  else:
    list_geo.append(geo)
  return list_geo
