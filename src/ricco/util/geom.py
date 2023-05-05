import json
import logging
import warnings

import geojson
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import wkb
from shapely import wkt
from shapely.errors import GeometryTypeError
from shapely.errors import ShapelyDeprecationWarning
from shapely.errors import WKBReadingError
from shapely.geometry import LinearRing
from shapely.geometry import LineString
from shapely.geometry import MultiLineString
from shapely.geometry import MultiPoint
from shapely.geometry import MultiPolygon
from shapely.geometry import Point
from shapely.geometry import Polygon
from shapely.geometry import shape
from shapely.geos import WKTReadingError
from simplejson.errors import JSONDecodeError

from ..util.util import ensure_list
from ..util.util import first_notnull_value

warnings.filterwarnings('ignore', category=ShapelyDeprecationWarning)

GeomTypeSet = (
  Point, MultiPoint,
  Polygon, MultiPolygon,
  LineString, MultiLineString,
  LinearRing
)


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


def get_epsg_by_lng(lng):
  """通过经度获取epsg代码"""
  lng_epsg_mapping = {
    # 中央经线和epsg代码的对应关系
    75: 4534, 78: 4535, 81: 4536, 84: 4537, 87: 4538,
    90: 4539, 93: 4540, 96: 4541, 99: 4542,
    102: 4543, 105: 4544, 108: 4545, 111: 4546,
    114: 4547, 117: 4548, 120: 4549, 123: 4550,
    126: 4551, 129: 4552, 132: 4553, 135: 4554,
  }
  lng = np.median(lng)
  key = min(lng_epsg_mapping.keys(), key=lambda x: abs(x - lng))
  return lng_epsg_mapping.get(key)


def get_lng_by_city(city: str):
  from ..resource.epsg_code import CITY_POINT
  if city in CITY_POINT.keys():
    return CITY_POINT[city]['lng']
  else:
    city += '市'
    if city in CITY_POINT.keys():
      return CITY_POINT[city]['lng']
    else:
      warnings.warn(f'请补充{city}的epsg信息，默认返回经度120')
      return 120


def get_epsg(city: str):
  """根据城市查询epsg代码，用于投影"""
  return get_epsg_by_lng(get_lng_by_city(city))


def projection(
    gdf: gpd.GeoDataFrame,
    epsg: int = None,
    city: str = None):
  """投影变换"""
  if not epsg:
    if city:
      epsg = get_epsg(city)
    else:
      lngs = gdf['geometry'].centroid.x.tolist()
      epsg = get_epsg_by_lng(lngs)
  return gdf.to_crs(epsg=epsg)


def projection_lnglat(lnglat, crs_from, crs_to):
  from pyproj import Transformer
  transformer = Transformer.from_crs(crs_from, crs_to)
  return transformer.transform(xx=lnglat[1], yy=lnglat[0])


def wkb_loads(x, hex=True):
  warnings.filterwarnings('ignore',
                          'Geometry column does not contain geometry.',
                          UserWarning)

  if pd.isna(x):
    return None

  try:
    return wkb.loads(x, hex=hex)
  except (AttributeError, WKBReadingError):
    return None


def wkb_dumps(x, hex=True, srid=4326) -> (str, None):
  if pd.isna(x):
    return None

  try:
    return wkb.dumps(x, hex=hex, srid=srid)
  except AttributeError:
    return None


def wkt_loads(x):
  if pd.isna(x):
    return None
  try:
    return wkt.loads(x)
  except (AttributeError, WKTReadingError):
    return None


def wkt_dumps(x) -> (str, None):
  if pd.isna(x):
    return None
  try:
    return wkt.dumps(x)
  except AttributeError:
    return None


def geojson_loads(x):
  """geojson文本形式转为shapely格式"""
  if pd.isna(x):
    return None
  try:
    geom = shape(geojson.loads(x))
    if geom.is_empty:
      return None
    return geom
  except (JSONDecodeError, AttributeError, GeometryTypeError, TypeError):
    return None


def geojson_dumps(x) -> (str, None):
  """shapely转为geojson文本格式"""
  if pd.isna(x):
    return None
  try:
    geom = geojson.Feature(geometry=x)
    return json.dumps(geom.geometry)
  except TypeError:
    return None


def is_shapely(x, na=False) -> bool:
  """判断是否为shapely格式"""
  if pd.isna(x):
    return na
  if type(x) in GeomTypeSet:
    return True
  else:
    return False


def is_wkb(x, na=False) -> bool:
  """判断是否为wkb格式"""
  if pd.isna(x):
    return na
  try:
    wkb.loads(x, hex=True)
    return True
  except WKBReadingError:
    return False


def is_wkt(x, na=False) -> bool:
  """判断是否为wkt格式"""
  if pd.isna(x):
    return na
  try:
    wkt.loads(x)
    return True
  except WKTReadingError:
    return False


def is_geojson(x, na=False) -> bool:
  """判断是否为geojson格式"""
  if pd.isna(x):
    return na
  try:
    if shape(geojson.loads(x)).is_empty:
      return False
    return True
  except (JSONDecodeError, AttributeError, GeometryTypeError, TypeError):
    return False


def infer_geom_format(x):
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


def ensure_multi_geom(geom):
  """将LineString和Polygon转为multi格式"""
  if geom.geom_type == 'LineString':
    return MultiLineString([geom])
  if geom.geom_type == 'Polygon':
    return MultiPolygon([geom])
  return geom


def multiline2multipolygon(multiline_shapely):
  """multiline转为multipolygon，直接首尾相连"""
  coords = []
  for line in multiline_shapely:
    lngs = line.xy[0]
    lats = line.xy[1]
    for i in range(len(lngs)):
      lng, lat = lngs[i], lats[i]
      point = Point((lng, lat))
      if len(coords) >= 1:
        if point != coords[-1]:
          coords.append(point)
      else:
        coords.append(point)
  return MultiPolygon([Polygon(coords)])


def geom_wkt2shapely(df, geometry='geometry',
                     epsg_code: int = 4326) -> gpd.GeoDataFrame:
  """wkt转gpd"""
  df[geometry] = df[geometry].apply(wkt_loads)
  return gpd.GeoDataFrame(df, geometry=geometry, crs=epsg_code)


def geom_wkb2lnglat(df, geometry='geometry', delete=False, within=False):
  """geometry转经纬度，求中心点经纬度"""
  df = geom_wkb2shapely(df, geometry=geometry)
  df = geom_shapely2lnglat(df, geometry=geometry, within=within, delete=delete)
  if not delete:
    df[geometry] = df[geometry].apply(wkb_dumps)
  return df


def get_inner_point(polygon: Polygon, within=True):
  """返回面内的一个点，默认返回中心点，当中心点不在面内则返回面内一个点"""
  if pd.isna(polygon):
    return None
  point = polygon.centroid
  if polygon.contains(point):
    return point
  else:
    if within:
      return polygon.representative_point()
    else:
      return point


def geom_wkt2wkb(df, geometry='geometry', epsg_code: int = 4326):
  """wkb转wkt"""
  df = geom_wkt2shapely(df, geometry=geometry, epsg_code=epsg_code)
  df[geometry] = df[geometry].apply(wkb_dumps)
  return df


def geom_wkb2shapely(df, geometry='geometry',
                     epsg_code: int = 4326) -> gpd.GeoDataFrame:
  """wkb直接转Dataframe"""
  df = df.copy()
  df[geometry] = df[geometry].apply(wkb_loads)
  return gpd.GeoDataFrame(df, geometry=geometry, crs=epsg_code)


def geom_lnglat2shapely(df, lng='lng', lat='lat', delete=True,
                        epsg_code: int = 4326) -> gpd.GeoDataFrame:
  """包含经纬度的DataFrame转GeoDataFrame"""
  from pandas.errors import SettingWithCopyWarning
  warnings.filterwarnings('ignore', category=SettingWithCopyWarning)
  df['geometry'] = df.apply(
      lambda d: Point((d[lng], d[lat])) if all([d[lng], d[lat]]) else None,
      axis=1
  )
  df = gpd.GeoDataFrame(df, crs=epsg_code)
  if delete:
    del df[lng], df[lat]
  return df


def geom_shapely2lnglat(df, geometry='geometry', within=False, delete=False):
  """
  shapely格式提取中心点转为经纬度。
  within: 范围的点是否再面内，默认False，直接返回中心点；
  当为True时，不在面内的中心点将用一个在面内的点代替
  """
  df['geometry_temp'] = df[geometry].apply(
      lambda x: get_inner_point(x, within=within) if x else None)
  df['lng'] = df['geometry_temp'].centroid.x
  df['lat'] = df['geometry_temp'].centroid.y
  del df['geometry_temp']
  if delete:
    del df[geometry]
  return df


def geom_lnglat2wkb(df, lng='lng', lat='lat', delete=False, code=4326):
  """经纬度转wkb格式的geometry"""
  df = geom_lnglat2shapely(df, 'lng', 'lat', delete=delete, epsg_code=code)
  df['geometry'] = df['geometry'].apply(wkb_dumps)
  if not delete:
    df = df.rename(columns={'lng': lng, 'lat': lat})
  return df


def geom_split_grids(df: gpd.GeoDataFrame, step: int, city: str = None):
  """
  根据所给边界划分固定边长的栅格

  Args:
      df: 边界文件，GeoDataFrame格式
      step: 栅格边长，单位：米
      city: 所属城市，用于投影

  Returns:

  """

  def get_xxyy(df):
    bounds_dict = df.bounds.T.to_dict()[0]
    minx = bounds_dict['minx']
    miny = bounds_dict['miny']
    maxx = bounds_dict['maxx']
    maxy = bounds_dict['maxy']
    xx = maxx - minx
    yy = maxy - miny
    return [xx, yy, minx, miny, maxx, maxy]

  def get_lnglat(df, i, j):
    _lng = df.loc[(df['i'] == i) &
                  (df['j'] == j), 'lng'].reset_index(drop=True)[0]
    _lat = df.loc[(df['i'] == i) &
                  (df['j'] == j), 'lat'].reset_index(drop=True)[0]
    return (_lng, _lat)

  def get_lnglat_sets(df, i, j):
    A = get_lnglat(df, i, j)
    B = get_lnglat(df, i, j + 1)
    C = get_lnglat(df, i + 1, j + 1)
    D = get_lnglat(df, i + 1, j)
    return Polygon((A, B, C, D, A))

  # 融合
  if not isinstance(df, gpd.GeoDataFrame):
    df = geom_wkb2shapely(df)
  df = df[['geometry']].dissolve()

  # 投影，获取实际的距离
  df_p = projection(df, city=city)

  # 分别获取投影前和投影后的点位及边长信息
  xy_o, xy_p = get_xxyy(df), get_xxyy(df_p)

  # 获取栅格的起止经纬度，步长等信息
  xr, yr = xy_o[0] / xy_p[0], xy_o[1] / xy_p[1]
  x_len, y_len = xr * step, yr * step
  x_num, y_num = int(xy_o[0] // x_len + 1), int(xy_o[1] // y_len + 1)
  logging.info(f'lng分段数：{x_num}，lat分段数：{y_num}')
  x_start, y_start = xy_o[2], xy_o[3]
  x_end, y_end = x_start + x_num * x_len, y_start + y_num * y_len

  # 构建经纬度列表
  lng_array, lat_array = np.linspace(x_start, x_end, num=x_num), np.linspace(
      y_start, y_end, num=y_num)
  lng_list, lat_list = list(lng_array), list(lat_array)

  # 构建栅格索引
  i_l, j_l, lng_l, lat_l = [], [], [], []
  for i, lng in enumerate(lng_list):
    for j, lat in enumerate(lat_list):
      i_l.append(i)
      j_l.append(j)
      lng_l.append(lng)
      lat_l.append(lat)
  df_temp = pd.DataFrame({'i': i_l, 'j': j_l, 'lng': lng_l, 'lat': lat_l})
  # 删除末尾的格子，避免后面出现out of range
  df_res = df_temp.loc[
    (df_temp['i'] != x_num - 1) & (df_temp['j'] != y_num - 1),
    ['i', 'j']].reset_index(drop=True)

  # 组合坐标集并转为Polygon
  df_res['geometry'] = df_res.apply(
      lambda df: get_lnglat_sets(df_temp, df['i'], df['j']), axis=1)

  # 生成grid_id列
  df_res['grid_id'] = df_res['i'].astype(str) + '-' + df_res['j'].astype(str)
  del df_res['i'], df_res['j']

  # 通过边界裁剪栅格
  df_res = gpd.GeoDataFrame(df_res, crs="epsg:4326")
  df.crs = 'epsg:4326'
  df_res = gpd.sjoin(df_res,
                     df,
                     how='inner',
                     predicate='intersects').drop('index_right', axis=1)

  # 将geometry转为wkb格式
  df_res['geometry'] = df_res['geometry'].apply(wkb_dumps)
  return df_res


def ensure_gdf(df, geometry='geometry'):
  geom = first_notnull_value(df[geometry])
  geom_format = infer_geom_format(geom)
  if geom_format == 'wkb':
    return geom_wkb2shapely(df, geometry=geometry)
  elif geom_format == 'wkt':
    return geom_wkt2shapely(df, geometry=geometry)
  elif geom_format == 'shapely':
    return gpd.GeoDataFrame(df, geometry=geometry)
  else:
    raise TypeError('未知的地理格式，支持wkb,wkt,shapely三种格式')


def mark_tags_v2(
    point_df: pd.DataFrame,
    polygon_df: pd.DataFrame,
    col_list: list = None,
    predicate='intersects',
    drop_geometry=False,
    geometry_format='wkb'):
  """
  使用面数据通过空间关联（sjoin）给点数据打标签

  Args:
      point_df: 点数据
      polygon_df: 面数据
      col_list: 面数据中要关联到结果中的列，若为空则全部关联
      predicate: 关联方法，默认'intersects'
      drop_geometry: 结果是否删除geometry，默认删除
      geometry_format: 输出的geometry格式，支持wkb,、wkt、shapely，默认wkb
  """
  if not col_list:
    col_list = polygon_df.columns.to_list()
  else:
    polygon_df = polygon_df[col_list + ['geometry']]

  col_list = ensure_list(col_list)
  for c in col_list:
    if c in point_df and c not in ['lng', 'lat', 'geometry']:
      c_n = f'{c}_origin'
      warnings.warn(f'点数据中存在面文件中待关联的列，已重命名：{c} --> {c_n}')
      point_df.rename(columns={c: c_n}, inplace=True)

  if 'geometry' in point_df:
    point_df = ensure_gdf(point_df)
    geom = first_notnull_value(point_df['geometry'])
    if geom.geom_type not in ['point', 'Point']:
      warnings.warn('左侧数据实际非点数据，将自动提取中心点进行关联')
      point_df['geometry_backup'] = point_df['geometry']
      point_df = geom_shapely2lnglat(point_df)
      point_df = geom_lnglat2shapely(point_df, delete=False)
  elif 'lng' in point_df and 'lat' in point_df:
    point_df = geom_lnglat2shapely(point_df, delete=False)
  else:
    raise KeyError('点文件中必须有经纬度或geometry')

  polygon_df = ensure_gdf(polygon_df)

  point_df = gpd.sjoin(
      point_df,
      polygon_df,
      how='left',
      predicate=predicate,
  ).drop('index_right', axis=1)

  if 'geometry_backup' in point_df:
    del point_df['geometry']
    point_df.rename(columns={'geometry_backup': 'geometry'}, inplace=True)

  if drop_geometry:
    del point_df['geometry']
  else:
    if geometry_format == 'wkb':
      point_df['geometry'] = point_df['geometry'].apply(wkb_dumps)
    elif geometry_format == 'wkt':
      point_df['geometry'] = point_df['geometry'].apply(wkt_dumps)
    elif geometry_format == 'shapely':
      pass
    else:
      raise ValueError('不支持的geometry格式')

  return pd.DataFrame(point_df)


def ensure_lnglat(lnglat) -> tuple:
  if isinstance(lnglat, (list, tuple)):
    if all([isinstance(i, (float, int)) for i in lnglat]):
      return lnglat
    else:
      raise TypeError('数据类型错误，经度和纬度都应该为数值型')
  if is_shapely(lnglat):
    geom = lnglat
  elif is_wkt(lnglat):
    geom = wkt_loads(lnglat)
  elif is_wkb(lnglat):
    geom = wkb_loads(lnglat)
  elif is_geojson(lnglat):
    geom = geojson_loads(lnglat)
  else:
    raise ValueError('未知的地理类型')
  return (geom.x, geom.y)


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
    epsg_to = get_epsg(city) if city else get_epsg_by_lng([p1[0], p2[0]])
  p1 = projection_lnglat(p1, epsg_from, epsg_to)
  p2 = projection_lnglat(p2, epsg_from, epsg_to)
  return Point(p1).distance(Point(p2))
