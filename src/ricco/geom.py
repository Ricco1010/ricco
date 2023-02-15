import logging
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import wkb
from shapely import wkt
from shapely.errors import ShapelyDeprecationWarning
from shapely.errors import WKBReadingError
from shapely.geometry import Point
from shapely.geometry import Polygon
from shapely.geos import WKTReadingError

from ricco.util import ensure_list
from ricco.util import first_notnull_value

warnings.filterwarnings('ignore', category=ShapelyDeprecationWarning)


def get_epsg(city):
  """
  查找citycode，用于投影
  """
  from ricco.config import EPSG_CODE
  if city in EPSG_CODE.keys():
    return EPSG_CODE[city]
  else:
    city = city + '市'
    if city in EPSG_CODE.keys():
      return EPSG_CODE[city]
    else:
      warnings.warn(
          "获取城市epsg失败，当前默认为32651。请在config.py中补充该城市")
      return 32651


def projection(gdf, proj_epsg: int = None, city: str = None):
  if not proj_epsg:
    if not city:
      raise ValueError(
          '获取投影信息失败，请补充参数:proj_epsg投影的坐标系统的epsg编号或city中国城市名称')
    else:
      proj_epsg = get_epsg(city)
  return gdf.to_crs(epsg=proj_epsg)


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


def wkb_dumps(x, hex=True, srid=4326):
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


def wkt_dumps(x):
  if pd.isna(x):
    return None
  try:
    return wkt.dumps(x)
  except AttributeError:
    return None


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


def is_shapely(x, na=False):
  from shapely.geometry import Point
  from shapely.geometry import MultiPoint
  from shapely.geometry import Polygon
  from shapely.geometry import MultiPolygon
  from shapely.geometry import LineString
  from shapely.geometry import MultiLineString
  from shapely.geometry import LinearRing

  geom_type_set = (
    Point, MultiPoint,
    Polygon, MultiPolygon,
    LineString, MultiLineString,
    LinearRing
  )
  if pd.isna(x):
    return na
  if type(x) in geom_type_set:
    return True
  else:
    return False


def is_geojson(x, na=False):
  # TODO(wangyukang): 未来考虑支持geojson格式
  pass


def infer_geom_format(x):
  if is_shapely(x):
    return 'shapely'
  if isinstance(x, str):
    # 尝试是否能成功转为wkb格式
    try:
      wkb.loads(x, hex=True)
      return 'wkb'
    except WKBReadingError:
      pass
    # 尝试是否能成功转为wkt格式
    try:
      wkt.loads(x)
      return 'wkt'
    except WKTReadingError:
      pass
  # TODO(wangyukang): 未来考虑支持geojson格式
  return 'unknown'


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
  使用面数据给点数据打标签

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


def dis_point2point(lnglat_ori: (tuple, str),
                    lnglat_dis: (tuple, str),
                    city: str,
                    crs_from: int = 4326,
                    crs_to: (str, int) = 'auto'):
  """
  计算两个点（经度，纬度）之间的距离，单位：米

  example:

  >>> dis_point2point((121.579051,31.3402), (121.581099,31.342405), '上海市')
  >>> 312.6011508211181

  :param lnglat_ori: 经纬度或wkb
  :param lnglat_dis: 经纬度或wkb
  :param city: 城市
  :param crs_from: 原始epsg，默认为4326
  :param crs_to: 投影epsg，默认为'auto',按城市自动获取
  :return:
  """
  # TODO(wangyukang): 目前会有性能问题，需优化
  from pyproj import Transformer
  from shapely.geometry import Point
  if crs_to == 'auto':
    crs_to = get_epsg(city)
  if isinstance(lnglat_ori, str):
    geom = wkb_loads(lnglat_ori)
    lnglat_ori = (geom.x, geom.y)
  if isinstance(lnglat_dis, str):
    geom = wkb_loads(lnglat_dis)
    lnglat_dis = (geom.x, geom.y)
  transformer = Transformer.from_crs(crs_from, crs_to)
  xy1 = transformer.transform(xx=lnglat_ori[1], yy=lnglat_ori[0])
  xy2 = transformer.transform(xx=lnglat_dis[1], yy=lnglat_dis[0])
  return Point(xy1).distance(Point(xy2))
