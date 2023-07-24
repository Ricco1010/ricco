import json
import logging
import warnings
from typing import List
from typing import Union

import geojson
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import wkb
from shapely import wkt
from shapely.errors import GeometryTypeError
from shapely.errors import ShapelyDeprecationWarning
from shapely.errors import WKBReadingError
from shapely.geometry import MultiLineString
from shapely.geometry import MultiPolygon
from shapely.geometry import Point
from shapely.geometry import Polygon
from shapely.geometry import shape
from shapely.geos import WKTReadingError
from simplejson.errors import JSONDecodeError
from tqdm import tqdm

from ..util.util import ensure_list
from ..util.util import first_notnull_value
from ..util.util import is_empty
from ..util.util import not_empty
from .decorator import geom_progress

warnings.filterwarnings('ignore', category=ShapelyDeprecationWarning)


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

  if is_empty(x):
    return

  try:
    return wkb.loads(x, hex=hex)
  except (AttributeError, WKBReadingError) as e:
    warnings.warn(f'{e}, 【{x}】')
    return


def wkb_dumps(x, hex=True, srid=4326) -> (str, None):
  if is_empty(x):
    return

  try:
    return wkb.dumps(x, hex=hex, srid=srid)
  except AttributeError as e:
    warnings.warn(f'{e}, 【{x}】')
    return


def wkt_loads(x):
  if is_empty(x):
    return
  try:
    return wkt.loads(x)
  except (AttributeError, WKTReadingError, TypeError) as e:
    warnings.warn(f'{e}, 【{x}】')
    return


def wkt_dumps(x) -> (str, None):
  if is_empty(x):
    return
  try:
    return wkt.dumps(x)
  except AttributeError as e:
    warnings.warn(f'{e}, 【{x}】')
    return


def geojson_loads(x):
  """geojson文本形式转为shapely格式"""
  if is_empty(x):
    return
  try:
    geom = shape(geojson.loads(x))
    if geom.is_empty:
      return
    return geom
  except (JSONDecodeError, AttributeError, GeometryTypeError, TypeError) as e:
    warnings.warn(f'{e}, 【{x}】')
    return


def geojson_dumps(x) -> (str, None):
  """shapely转为geojson文本格式"""
  if is_empty(x):
    return
  try:
    geom = geojson.Feature(geometry=x)
    return json.dumps(geom.geometry)
  except TypeError as e:
    warnings.warn(f'{e}, 【{x}】')
    return


def is_shapely(x, na=False) -> bool:
  """判断是否为shapely格式"""
  from ..resource.geometry import GeomTypeSet
  if pd.isna(x):
    return na
  if type(x) in GeomTypeSet:
    return True
  else:
    return False


def is_wkb(x, na=False) -> bool:
  """判断是否为wkb格式"""
  if not isinstance(x, str):
    return False
  if pd.isna(x):
    return na
  try:
    wkb.loads(x, hex=True)
    return True
  except WKBReadingError:
    return False


def is_wkt(x, na=False) -> bool:
  """判断是否为wkt格式"""
  if not isinstance(x, str):
    return False
  if pd.isna(x):
    return na
  try:
    wkt.loads(x)
    return True
  except WKTReadingError:
    return False


def is_geojson(x, na=False) -> bool:
  """判断是否为geojson格式"""
  if not isinstance(x, (str, dict)):
    return False
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
  try:
    return MultiPolygon([Polygon(coords)])
  except ValueError as e:
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


@geom_progress
def geom_wkb2shapely(df, geometry='geometry',
                     epsg_code: int = 4326) -> gpd.GeoDataFrame:
  df = df.copy()
  df[geometry] = df[geometry].progress_apply(wkb_loads)
  return gpd.GeoDataFrame(df, geometry=geometry, crs=epsg_code)


@geom_progress
def geom_shapely2wkb(df, geometry='geometry'):
  df[geometry] = df[geometry].progress_apply(wkb_dumps)
  return df


@geom_progress
def geom_wkt2shapely(df, geometry='geometry',
                     epsg_code: int = 4326) -> gpd.GeoDataFrame:
  df[geometry] = df[geometry].progress_apply(wkt_loads)
  return gpd.GeoDataFrame(df, geometry=geometry, crs=epsg_code)


@geom_progress
def geom_shapely2wkt(df, geometry='geometry'):
  df[geometry] = df[geometry].progress_apply(wkt_dumps)
  return df


@geom_progress
def geom_lnglat2shapely(df,
                        lng='lng',
                        lat='lat',
                        geometry='geometry',
                        delete=True,
                        epsg_code: int = 4326) -> gpd.GeoDataFrame:
  from pandas.errors import SettingWithCopyWarning
  warnings.filterwarnings('ignore', category=SettingWithCopyWarning)

  df[geometry] = df.progress_apply(
      lambda d: Point((d[lng], d[lat]))
      if not_empty(d[lng]) and not_empty(d[lat])
      else None,
      axis=1
  )
  df = gpd.GeoDataFrame(df, crs=epsg_code)
  if delete:
    del df[lng], df[lat]
  return df


@geom_progress
def geom_shapely2lnglat(df, geometry='geometry',
                        lng='lng', lat='lat',
                        within=False, delete=False):
  """
  shapely格式提取中心点转为经纬度。
  within: 范围的点是否再面内，默认False，直接返回中心点；
  当为True时，不在面内的中心点将用一个在面内的点代替
  """

  def get_xy(x):
    p = get_inner_point(x, within=within)
    return p.centroid.x, p.centroid.y

  df[[lng, lat]] = df[[geometry]].progress_apply(
      lambda r: get_xy(r[geometry]) if r[geometry] else (None, None),
      result_type='expand',
      axis=1
  )
  if delete:
    del df[geometry]
  return df


def geom_wkb2lnglat(df, geometry='geometry', delete=False, within=False):
  """geometry转经纬度，求中心点经纬度"""
  df = geom_wkb2shapely(df, geometry=geometry)
  df = geom_shapely2lnglat(df, geometry=geometry, within=within, delete=delete)
  if not delete:
    df = geom_shapely2wkb(df, geometry=geometry)
  return df


def geom_lnglat2wkb(df,
                    lng='lng',
                    lat='lat',
                    geometry='geometry',
                    delete=False, code=4326):
  """经纬度转wkb格式的geometry"""
  df = geom_lnglat2shapely(
      df, 'lng', 'lat', geometry=geometry, delete=delete, epsg_code=code
  )
  df = geom_shapely2wkb(df, geometry=geometry)
  if not delete:
    df = df.rename(columns={'lng': lng, 'lat': lat})
  return df


def geom_wkt2lnglat(df, geometry='geometry', delete=False, within=False):
  """geometry转经纬度，求中心点经纬度"""
  df = geom_wkt2shapely(df, geometry=geometry)
  df = geom_shapely2lnglat(df, geometry=geometry, within=within, delete=delete)
  if not delete:
    df = geom_shapely2wkt(df, geometry=geometry)
  return df


def geom_lnglat2wkt(df,
                    lng='lng',
                    lat='lat',
                    geometry='geometry',
                    delete=False, code=4326):
  """经纬度转wkb格式的geometry"""
  df = geom_lnglat2shapely(
      df, 'lng', 'lat', geometry=geometry, delete=delete, epsg_code=code
  )
  df = geom_shapely2wkt(df, geometry=geometry)
  if not delete:
    df = df.rename(columns={'lng': lng, 'lat': lat})
  return df


def geom_wkb2wkt(df, geometry='geometry', epsg_code: int = 4326):
  """wkb转wkt"""
  df = geom_wkb2shapely(df, geometry=geometry, epsg_code=epsg_code)
  return geom_shapely2wkt(df, geometry=geometry)


def geom_wkt2wkb(df, geometry='geometry', epsg_code: int = 4326):
  """wkb转wkt"""
  df = geom_wkt2shapely(df, geometry=geometry, epsg_code=epsg_code)
  return geom_shapely2wkb(df, geometry=geometry)


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
  tqdm.pandas(desc='lnglat2shapely')
  df_res['geometry'] = df_res.progress_apply(
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
  tqdm.pandas(desc='shapely2wkb')
  df_res['geometry'] = df_res['geometry'].progress_apply(wkb_dumps)
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
    geometry_format='wkb',
    warning_message=True):
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
    col_list = ensure_list(col_list)
    polygon_df = polygon_df[[*col_list, 'geometry']]

  for c in col_list:
    if c in point_df and c not in ['lng', 'lat', 'geometry']:
      c_n = f'{c}_origin'
      if warning_message:
        warnings.warn(f'点数据中存在面文件中待关联的列，已重命名：{c} --> {c_n}')
      point_df.rename(columns={c: c_n}, inplace=True)

  if 'geometry' in point_df:
    point_df = ensure_gdf(point_df)
    geom = first_notnull_value(point_df['geometry'])
    if geom.geom_type not in ['point', 'Point']:
      if warning_message:
        warnings.warn('左侧数据实际非点数据，将自动提取中心点进行关联')
      point_df['geometry_backup'] = point_df['geometry']
      point_df = geom_shapely2lnglat(point_df, within=True)
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
      point_df = geom_shapely2wkb(point_df)
    elif geometry_format == 'wkt':
      point_df = geom_shapely2wkt(point_df)
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


def buffer(df: pd.DataFrame, radius: Union[int, float],
           city: str = None,
           geo_type: str = 'point',
           geometry: str = 'geometry',
           buffer_geometry: str = 'buffer_geometry',
           geo_format='wkb') -> pd.DataFrame:
  """
  获得一定半径的缓冲区

  Args:
    df: pd.DataFrame, 包含地理信息的DataFrame
    radius: numeric, 缓冲区半径（单位米）
    city: str, 可选, 投影城市，可提高数据精度
    geo_type: str, 地理数据类型，可选point, line或polygon(包括multipolygon)，默认point
    geometry: str, geometry字段名，默认"geometry"
    buffer_geometry: 输出的缓冲区geometry字段名，默认"buffer_geometry"
    geo_format: str, 输出的缓冲区geometry格式，支持"wkb","wkt","shapely"，默认"wkb"

  Returns: 包含缓冲区geometry的DataFrame

  Examples:
    >>> df = pd.DataFrame({'id': [1, 2, 3],
    >>>                    'lng': [116.18601, 116.18366, 116.18529],
    >>>                    'lat': [40.02894, 40.03550, 40.03565]})

    >>> df
        id        lng       lat
    0   1  116.18601  40.02894
    1   2  116.18366  40.03550
    2   3  116.18529  40.03565

    >>> buffer(df=df, radius=1500, city='北京', geo_type='point')
        id        lng       lat                                    buffer_geometry
    0   1  116.18601  40.02894  0103000020E6100000010000004100000092A0207A070D...
    1   2  116.18366  40.03550  0103000020E6100000010000004100000071178800E10C...
    2   3  116.18529  40.03565  0103000020E610000001000000410000008A2570B5FB0C...

  """
  df = df.reset_index(drop=True)
  cols = []
  if geometry in df:
    cols.append(geometry)
  if 'lng' in df and 'lat' in df:
    cols.extend(['lng', 'lat'])
  df_tmp = df[cols]
  df_tmp.rename(columns={geometry: 'geometry'}, inplace=True)

  if geo_type == 'point':
    if 'geometry' in df_tmp:
      df_tmp = ensure_gdf(df_tmp)
      geom = first_notnull_value(df_tmp['geometry'])
      if geom.geom_type not in ['point', 'Point']:
        warnings.warn('数据实际非点数据，将自动提取中心点进行关联')
        df_tmp = geom_shapely2lnglat(df_tmp)
        df_tmp = geom_lnglat2shapely(df_tmp, delete=False)
    elif 'lng' in df_tmp and 'lat' in df_tmp:
      df_tmp = geom_lnglat2shapely(df_tmp, delete=False)

    else:
      raise KeyError('点文件中必须有经纬度或geometry')
  elif geo_type == 'line' or geo_type == 'polygon':
    df_tmp = ensure_gdf(df_tmp, geometry=geometry)
  else:
    raise ValueError('geo_type必须为point，line或polygon')
  df_buffer = df_tmp[['geometry']]

  df_buffer = projection(df_buffer, city=city)
  df_buffer['geometry'] = df_buffer.geometry.buffer(radius)
  df_buffer = projection(df_buffer, epsg=4326)
  if geo_format == 'wkb':
    tqdm.pandas(desc='shapely2wkb')
    df_buffer['geometry'] = df_buffer['geometry'].progress_apply(wkb_dumps)
  elif geo_format == 'wkt':
    tqdm.pandas(desc='shapely2wkt')
    df_buffer['geometry'] = df_buffer['geometry'].progress_apply(wkt_dumps)
  elif geo_format == 'shapely':
    pass
  else:
    raise ValueError('不支持的geometry格式')
  df_buffer.rename(columns={'geometry': buffer_geometry}, inplace=True)
  df = df.join(df_buffer, how='left')

  return df


def spatial_agg(point_df: pd.DataFrame, polygon_df: pd.DataFrame,
                by: Union[str, List[str]],
                agg: dict,
                polygon_geometry: str = 'geometry') -> pd.DataFrame:
  """
  对面数据覆盖范围内的点数据进行空间统计
  Args:
    point_df: pd.DataFrame, 点数据dataframe;
    polygon_df: pd.DataFrame, 面数据dataframe;
    by: Union[str, List[str]], 空间统计单位字段；
    agg: dict, 空间统计操作。格式为{'被统计字段名': '操作名', ...}的字典。如{'poi':'sum'};
    polygon_geometry: str, 面数据geometry字段名，默认"geometry";

  Returns: pd.DataFrame, 包含空间统计单位字段和被统计字段和面数据geometry的DataFrame
  """

  polygon_df.rename({polygon_geometry: 'geometry'}, inplace=True)
  polygon_df = polygon_df[[by, 'geometry']]
  point_df = mark_tags_v2(polygon_df=polygon_df, point_df=point_df,
                          drop_geometry=True)
  df_grouped = point_df.groupby(by=by, as_index=False).agg(agg)

  return df_grouped
