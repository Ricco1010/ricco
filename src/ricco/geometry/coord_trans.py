import math

import geojson.utils
from shapely.geometry.base import BaseGeometry
from shapely.geometry.base import BaseMultipartGeometry
from shapely.ops import transform as sh_transform
from tqdm import tqdm

from ..util.util import is_empty
from .df import _ensure_geometry
from .df import shapely2x
from .util import infer_geom_format

earthR = 6378245.0
x_pi = math.pi * 3000.0 / 180.0


class SRS:
  """空间参考系统(Spatial Reference System)"""
  #: 世界大地测量系统 (World Geodetic System 1984)
  wgs84 = 'wgs84'
  #: 百度坐标系
  bd09 = 'bd09'
  #: 国测局坐标（或火星坐标）
  gcj02 = 'gcj02'


def outOfChina(lat, lng):
  return not (72.004 <= lng <= 137.8347 and 0.8293 <= lat <= 55.8271)


def transform(x, y):
  xy = x * y
  absX = math.sqrt(abs(x))
  xPi = x * math.pi
  yPi = y * math.pi
  d = 20.0 * math.sin(6.0 * xPi) + 20.0 * math.sin(2.0 * xPi)

  lat = d
  lng = d

  lat += 20.0 * math.sin(yPi) + 40.0 * math.sin(yPi / 3.0)
  lng += 20.0 * math.sin(xPi) + 40.0 * math.sin(xPi / 3.0)

  lat += 160.0 * math.sin(yPi / 12.0) + 320 * math.sin(yPi / 30.0)
  lng += 150.0 * math.sin(xPi / 12.0) + 300.0 * math.sin(xPi / 30.0)

  lat *= 2.0 / 3.0
  lng *= 2.0 / 3.0

  lat += -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * xy + 0.2 * absX
  lng += 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * xy + 0.1 * absX

  return lat, lng


def delta(lat, lng):
  ee = 0.00669342162296594323
  dLat, dLng = transform(lng - 105.0, lat - 35.0)
  radLat = lat / 180.0 * math.pi
  magic = math.sin(radLat)
  magic = 1 - ee * magic * magic
  sqrtMagic = math.sqrt(magic)
  dLat = (dLat * 180.0) / ((earthR * (1 - ee)) / (magic * sqrtMagic) * math.pi)
  dLng = (dLng * 180.0) / (earthR / sqrtMagic * math.cos(radLat) * math.pi)
  return dLat, dLng


def wgs2gcj(wgsLat, wgsLng):
  if outOfChina(wgsLat, wgsLng):
    return wgsLat, wgsLng
  dlat, dlng = delta(wgsLat, wgsLng)
  return wgsLat + dlat, wgsLng + dlng


def gcj2wgs(gcjLat, gcjLng):
  if outOfChina(gcjLat, gcjLng):
    return gcjLat, gcjLng
  dlat, dlng = delta(gcjLat, gcjLng)
  return gcjLat - dlat, gcjLng - dlng


def gcj2bd(gcjLat, gcjLng):
  if outOfChina(gcjLat, gcjLng):
    return gcjLat, gcjLng
  x = gcjLng
  y = gcjLat
  z = math.hypot(x, y) + 0.00002 * math.sin(y * x_pi)
  theta = math.atan2(y, x) + 0.000003 * math.cos(x * x_pi)
  bdLng = z * math.cos(theta) + 0.0065
  bdLat = z * math.sin(theta) + 0.006
  return bdLat, bdLng


def bd2gcj(bdLat, bdLng):
  if outOfChina(bdLat, bdLng):
    return bdLat, bdLng
  x = bdLng - 0.0065
  y = bdLat - 0.006
  z = math.hypot(x, y) - 0.00002 * math.sin(y * x_pi)
  theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
  gcjLng = z * math.cos(theta)
  gcjLat = z * math.sin(theta)
  return gcjLat, gcjLng


def wgs2bd(wgsLat, wgsLng):
  return gcj2bd(*wgs2gcj(wgsLat, wgsLng))


def bd2wgs(bdLat, bdLng):
  return gcj2wgs(*bd2gcj(bdLat, bdLng))


_fn_mapping = {
  (SRS.bd09, SRS.wgs84): bd2wgs,
  (SRS.gcj02, SRS.wgs84): gcj2wgs,
  (SRS.wgs84, SRS.bd09): wgs2bd,
  (SRS.gcj02, SRS.bd09): gcj2bd,
  (SRS.wgs84, SRS.gcj02): wgs2gcj,
  (SRS.bd09, SRS.gcj02): bd2gcj,
}


def _coord_transform(lng: float, lat: float, from_srs: (SRS, str),
                     to_srs: (SRS, str)):
  """
  坐标系转换
  Args:
    lng: 输入的经度
    lat: 输入的纬度
    from_srs: 输入坐标的格式
    to_srs: 输出坐标的格式
  """
  if from_srs == to_srs:
    return lng, lat

  if is_empty(lng) or is_empty(lat):
    return None, None

  key = (from_srs, to_srs)
  if key not in _fn_mapping:
    raise NotImplementedError(
        'not support transformation from %s to %s' % (from_srs, to_srs))
  lat, lng = _fn_mapping[key](lat, lng)
  return lng, lat


def coord_transform_geojson(obj: dict, from_srs: SRS, to_srs: SRS):
  """对GeoJSON格式内的所有坐标点执行坐标系转换

  Examples:
    point_bd09 = Point([1, 2])
    geojson = mapping(point_bd09)
    transformed = coord_transform(geojson, SRS.bd09, SRS.wgs84)
    point_wgs84 = shape(transformed)
  """
  return geojson.utils.map_tuples(
      lambda c: _coord_transform(c[0], c[1], from_srs, to_srs), obj)


def _coord_transform_geometry(geo: (BaseGeometry, BaseMultipartGeometry),
                              from_srs: SRS,
                              to_srs: SRS):
  """对Geomery内的所有点进行坐标转换，返回转换后的Geometry

  该方法可以支持所有的Shapely Geometry形状，包括Point, Line, Polygon,
  MultiPloygon等，返回的Geometry和输入的形状保持一致
  Args:
    geo: 输入的shapely Geometry
    from_srs: 输入的坐标格式
    to_srs: 输出的坐标格式
  Returns:
    转换后的shapely Geometry
  """
  return sh_transform(
      lambda x, y, z=None: _coord_transform(x, y, from_srs, to_srs), geo)


def coord_trans_x2y(df,
                    srs_from: (SRS, str),
                    srs_to: (SRS, str),
                    c_lng: str = 'lng',
                    c_lat: str = 'lat'):
  """
  经纬度类型坐标坐标批量转换工具
  Args:
    df: 输入的dataframe，必须要有geometry列
    srs_from: 当前坐标系，可选wgs84,bd09,gcj02
    srs_to: 要转的坐标系，可选wgs84,bd09,gcj02
    c_lng: 经度列名
    c_lat: 纬度列名
  """
  df = df.copy()
  tqdm.pandas(desc=f'{srs_from}-->{srs_to}')
  df[[c_lng, c_lat]] = df.progress_apply(
      lambda r: _coord_transform(r[c_lng], r[c_lat], srs_from, srs_to),
      axis=1, result_type='expand'
  )
  return df


def coord_trans_geom(df,
                     srs_from: (SRS, str),
                     srs_to: (SRS, str),
                     c_geometry: str = 'geometry',
                     geometry_format=None):
  """
  geometry类型坐标批量转换工具
  Args:
    df: 输入的dataframe，必须要有geometry列
    srs_from: 当前坐标系，可选wgs84,bd09,gcj02
    srs_to: 要转的坐标系，可选wgs84,bd09,gcj02
    c_geometry: 要转换的geometry列名
    geometry_format: 指定要输出的geometry格式，默认返回和原来相同的geometry格式
  """

  assert c_geometry in df
  df = df.copy()
  if not geometry_format:
    geometry_format = infer_geom_format(df[c_geometry])
  df_temp = _ensure_geometry(df)
  tqdm.pandas(desc=f'{srs_from}-->{srs_to}')
  df_temp[c_geometry] = df_temp[c_geometry].progress_apply(
      lambda x: _coord_transform_geometry(x, srs_from, srs_to)
  )
  del df[c_geometry]
  df = df.join(df_temp[[c_geometry]], how='left')
  return shapely2x(df, geometry_format=geometry_format, geometry=c_geometry)


def coord_transformer(df,
                      srs_from: (SRS, str),
                      srs_to: (SRS, str),
                      c_lng: str = 'lng',
                      c_lat: str = 'lat',
                      c_geometry: str = 'geometry',
                      geometry_format=None):
  """
  坐标转换工具，优先转geometry列
  Args:
    df: 输入的dataframe，必须要有geometry列
    srs_from: 当前坐标系，可选wgs84,bd09,gcj02
    srs_to: 要转的坐标系，可选wgs84,bd09,gcj02
    c_lng: 经度列名
    c_lat: 纬度列名
    c_geometry: 要转换的geometry列名
    geometry_format: 指定要输出的geometry格式，默认返回和原来相同的geometry格式
  """
  if c_geometry in df:
    return coord_trans_geom(df, srs_from, srs_to, c_geometry, geometry_format)
  elif c_lat in df and c_lng in df:
    return coord_trans_x2y(df, srs_from, srs_to, c_lng, c_lat)
  else:
    raise KeyError(f'文件中必须有经纬度列或"{c_geometry}"列')
