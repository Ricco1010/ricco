import logging
import warnings
from typing import List
from typing import Union

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point
from shapely.geometry import Polygon
from tqdm import tqdm

from ..etl.transformer import split_list_to_row
from ..util.decorator import progress
from ..util.util import ensure_list
from ..util.util import first_notnull_value
from ..util.util import is_empty
from ..util.util import not_empty
from .util import ensure_multi_geom
from .util import geojson_dumps
from .util import geojson_loads
from .util import get_epsg
from .util import get_epsg_by_lng
from .util import infer_geom_format
from .util import wkb_dumps
from .util import wkb_loads
from .util import wkt_dumps
from .util import wkt_loads


def projection(
    gdf: gpd.GeoDataFrame,
    epsg: int = None,
    city: str = None,
    geometry='geometry') -> gpd.GeoDataFrame:
  """
  投影变换
  Args:
    gdf: 输入的GeomDataFrame格式的数据
    epsg: epsg code, 第一优先级
    city: 城市名称，未传入epsg的情况下将通过城市名称获取epsg，若二者都为空则根据经纬度获取
    geometry: geometry列名
  """
  if not epsg:
    epsg = get_epsg(city) if city else get_epsg_by_lng(
        gdf[geometry].centroid.x.tolist()
    )
  return gdf.to_crs(epsg=epsg)


@progress
def wkb2shapely(df,
                geometry='geometry',
                epsg_code: int = 4326) -> gpd.GeoDataFrame:
  df = df.copy()
  df[geometry] = df[geometry].progress_apply(wkb_loads)
  return gpd.GeoDataFrame(df, geometry=geometry, crs=epsg_code)


@progress
def shapely2wkb(df, geometry='geometry'):
  df = pd.DataFrame(df).copy()
  df[geometry] = df[geometry].progress_apply(wkb_dumps)
  return df


@progress
def wkt2shapely(df,
                geometry='geometry',
                epsg_code: int = 4326) -> gpd.GeoDataFrame:
  df = df.copy()
  df[geometry] = df[geometry].progress_apply(wkt_loads)
  return gpd.GeoDataFrame(df, geometry=geometry, crs=epsg_code)


@progress
def shapely2wkt(df, geometry='geometry'):
  df = pd.DataFrame(df).copy()
  df[geometry] = df[geometry].progress_apply(wkt_dumps)
  return df


@progress
def geojson2shapely(df,
                    geometry='geometry',
                    epsg_code: int = 4326) -> gpd.GeoDataFrame:
  df = df.copy()
  df[geometry] = df[geometry].progress_apply(geojson_loads)
  return gpd.GeoDataFrame(df, geometry=geometry, crs=epsg_code)


@progress
def shapely2geojson(df, geometry='geometry'):
  df = pd.DataFrame(df).copy()
  df[geometry] = df[geometry].progress_apply(geojson_dumps)
  return df


@progress
def lnglat2shapely(df,
                   lng='lng',
                   lat='lat',
                   geometry='geometry',
                   delete=True,
                   epsg_code: int = 4326) -> gpd.GeoDataFrame:
  df = df.copy()
  df[geometry] = df.progress_apply(
      lambda d: Point(d[lng], d[lat])
      if not_empty(d[lng]) and not_empty(d[lat])
      else None,
      axis=1
  )
  df = gpd.GeoDataFrame(df, crs=epsg_code, geometry=geometry)
  if delete:
    del df[lng], df[lat]
  return df


def shapely2lnglat(df,
                   geometry='geometry',
                   lng='lng',
                   lat='lat',
                   within=False,
                   delete=False):
  """
  shapely格式提取面内点转为经纬度。
  Args:
    df: 要转换的DataFrame
    geometry: 输入的geometry列名
    lng: 输出的经度列名
    lat: 输出的纬度列名
    within: 范围的点是否再面内
      - False(default): 直接返回中心点；
      - True: 返回面内的一个点
    delete: 是否删除geometry
  """

  df = df.copy()
  if within:
    df[lng] = df.representative_point().x
    df[lat] = df.representative_point().y
  else:
    df[lng] = df.centroid.x
    df[lat] = df.centroid.y
  if delete:
    del df[geometry]
  return df


def wkb2lnglat(df, geometry='geometry', delete=False, within=False):
  """geometry转经纬度，求中心点经纬度"""
  df = wkb2shapely(df, geometry=geometry)
  df = shapely2lnglat(df, geometry=geometry, within=within, delete=delete)
  if not delete:
    df = shapely2wkb(df, geometry=geometry)
  return df


def lnglat2wkb(df,
               lng='lng',
               lat='lat',
               geometry='geometry',
               delete=False, code=4326):
  """经纬度转wkb格式的geometry"""
  df = lnglat2shapely(
      df, lng, lat, geometry=geometry, delete=delete, epsg_code=code
  )
  df = shapely2wkb(df, geometry=geometry)
  return df


def wkt2lnglat(df, geometry='geometry', delete=False, within=False):
  """geometry转经纬度，求中心点经纬度"""
  df = wkt2shapely(df, geometry=geometry)
  df = shapely2lnglat(df, geometry=geometry, within=within, delete=delete)
  if not delete:
    df = shapely2wkt(df, geometry=geometry)
  return df


def lnglat2wkt(df,
               lng='lng',
               lat='lat',
               geometry='geometry',
               delete=False, code=4326):
  """经纬度转wkb格式的geometry"""
  df = lnglat2shapely(
      df, lng, lat, geometry=geometry, delete=delete, epsg_code=code
  )
  df = shapely2wkt(df, geometry=geometry)
  return df


def wkb2wkt(df, geometry='geometry', epsg_code: int = 4326):
  """wkb转wkt"""
  df = wkb2shapely(df, geometry=geometry, epsg_code=epsg_code)
  return shapely2wkt(df, geometry=geometry)


def wkt2wkb(df, geometry='geometry', epsg_code: int = 4326):
  """wkb转wkt"""
  df = wkt2shapely(df, geometry=geometry, epsg_code=epsg_code)
  return shapely2wkb(df, geometry=geometry)


def shapely2central_shapely(df, geometry='geometry', within=False):
  """获取中心点shapely格式"""
  df = shapely2lnglat(df, geometry=geometry, within=within)
  return lnglat2shapely(df, geometry=geometry, delete=True)


def auto2shapely(df, geometry='geometry') -> gpd.GeoDataFrame:
  """自动识别地理格式并转换为shapely格式"""
  geom_format = infer_geom_format(df[geometry])
  assert geom_format in ('wkb', 'wkt', 'shapely', 'geojson'), '未知的地理格式'
  if geom_format == 'geojson':
    return geojson2shapely(df, geometry=geometry)
  if geom_format == 'wkb':
    return wkb2shapely(df, geometry=geometry)
  if geom_format == 'wkt':
    return wkt2shapely(df, geometry=geometry)
  if geom_format == 'shapely':
    return gpd.GeoDataFrame(df, geometry=geometry)


def shapely2x(df: (gpd.GeoDataFrame, pd.DataFrame),
              geometry_format: str,
              geometry='geometry'):
  """
  将shapely转为指定的格式
  Args:
    df: 要转换的GeoDataFrame
    geometry_format: 支持wkb,wkt,shapely,geojson
    geometry: geometry列的列名，默认“geometry”
  """
  assert geometry_format in ('wkb', 'wkt', 'shapely', 'geojson'), '未知的地理格式'

  if geometry_format == 'geojson':
    return shapely2geojson(df, geometry=geometry)
  if geometry_format == 'wkb':
    return shapely2wkb(df, geometry=geometry)
  if geometry_format == 'wkt':
    return shapely2wkt(df, geometry=geometry)
  if geometry_format == 'shapely':
    return gpd.GeoDataFrame(df, geometry=geometry)


def auto2x(df, geometry_format: str, geometry='geometry'):
  """
  将geometry转为指定格式
  Args:
    df: 要转换的Dataframe
    geometry_format: 要转换为的geometry类型，支持shapely,wkb,wkt,geojson
    geometry: geometry列的列名，默认为“geometry”
  """
  if infer_geom_format(df[geometry]) == geometry_format:
    return df
  df = auto2shapely(df, geometry=geometry)
  return shapely2x(df, geometry_format=geometry_format, geometry=geometry)


def distance_min(geometry, gdf: gpd.GeoDataFrame) -> float:
  """
  计算单个geometry到数据集gdf中元素的最短距离
  Args:
    geometry: 单个geometry，shapely格式
    gdf: 数据集，GeoDataFrame格式
  """
  return gdf.distance(geometry).min()


@progress
def distance_gdf(df: gpd.GeoDataFrame, df_target: gpd.GeoDataFrame, c_dst: str,
                 left_geometry='geometry'):
  """计算一个数据集中的每个元素到另一个数据集之间的最短距离"""
  df = df.copy()
  df[c_dst] = df[left_geometry].progress_apply(
      lambda p: distance_min(p, df_target) if not_empty(p) else np.nan
  )
  return df


def split_grids(df: gpd.GeoDataFrame, step: int, city: str = None):
  """
  根据所给边界划分固定边长的栅格

  Args:
    df: 边界文件，GeoDataFrame格式
    step: 栅格边长，单位：米
    city: 所属城市，用于投影
  """

  def get_xxyy(_df):
    bounds_dict = _df.bounds.T.to_dict()[0]
    minx = bounds_dict['minx']
    miny = bounds_dict['miny']
    maxx = bounds_dict['maxx']
    maxy = bounds_dict['maxy']
    xx = maxx - minx
    yy = maxy - miny
    return [xx, yy, minx, miny, maxx, maxy]

  def get_lnglat(_df, _i, _j):
    _lng = _df.loc[(_df['i'] == _i) &
                   (_df['j'] == _j), 'lng'].reset_index(drop=True)[0]
    _lat = _df.loc[(_df['i'] == _i) &
                   (_df['j'] == _j), 'lat'].reset_index(drop=True)[0]
    return _lng, _lat

  def get_lnglat_sets(_df, _i, _j):
    a = get_lnglat(_df, _i, _j)
    b = get_lnglat(_df, _i, _j + 1)
    c = get_lnglat(_df, _i + 1, _j + 1)
    d = get_lnglat(_df, _i + 1, _j)
    return Polygon((a, b, c, d, a))

  # 融合
  if not isinstance(df, gpd.GeoDataFrame):
    df = wkb2shapely(df)
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
  tqdm.pandas(desc='lnglats2shapelyPolygon')
  df_res['geometry'] = df_res.progress_apply(
      lambda r: get_lnglat_sets(df_temp, r['i'], r['j']), axis=1)

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
  df_res = shapely2wkb(df_res)
  return df_res


def _ensure_geometry(_df,
                     ensure_point=False,
                     warning_message=False,
                     geometry='geometry',
                     lng='lng',
                     lat='lat'):
  """转换并仅保留geometry列"""
  if geometry in _df:
    _df = auto2shapely(_df[[geometry]], geometry=geometry)[[geometry]]
    if ensure_point:
      geom = first_notnull_value(_df[geometry])
      if geom.geom_type not in ['point', 'Point']:
        if warning_message:
          warnings.warn('非点数据，提取面内点')
        _df = shapely2central_shapely(_df, within=True, geometry=geometry)
    return _df

  if lng in _df and lat in _df:
    return lnglat2shapely(
        _df[[lng, lat]],
        lng=lng, lat=lat,
        geometry=geometry,
        delete=False,
    )[[geometry]]

  raise KeyError(f'文件中必须有{lng},{lat}列或{geometry}列')


def mark_tags_v2(
    point_df: pd.DataFrame,
    polygon_df: pd.DataFrame,
    col_list: list = None,
    *,
    predicate='intersects',
    drop_geometry=False,
    geometry_format='wkb',
    warning_message=True,
    point_lng='lng',
    point_lat='lat',
    point_geometry='geometry',
    polygon_geometry='geometry',
):
  """
  使用面数据通过空间关联（sjoin）给数据打标签
  Args:
    point_df: 点数据
    polygon_df: 面数据
    col_list: 面数据中要关联到结果中的列，若为空则全部关联
    predicate: 关联方法，默认'intersects'
    drop_geometry: 结果是否删除geometry，默认删除
    geometry_format: 输出的geometry格式，支持wkb,wkt,shapely,geojson，默认wkb
    warning_message: 是否输出警告信息
    point_lng: 指定点数据的经度列名
    point_lat: 指定点数据的经度列名
    point_geometry: 指定点数据的geometry列名
    polygon_geometry: 指定面数据的geometry列名
  """
  point_df = point_df.copy()
  assert point_df.index.is_unique, 'point_df索引列必须唯一'
  if not col_list:
    col_list = polygon_df.columns.to_list()
  else:
    col_list = ensure_list(col_list)
    polygon_df = polygon_df[[*col_list, polygon_geometry]]

  for c in col_list:
    if c in point_df and c not in [point_lng, point_lat, point_geometry]:
      c_n = f'{c}_origin'
      if warning_message:
        warnings.warn(f'点数据中存在面文件中待关联的列，已重命名：{c} --> {c_n}')
      point_df.rename(columns={c: c_n}, inplace=True)
  # 转换为shapely格式
  df = _ensure_geometry(point_df, True, warning_message,
                        lng=point_lng, lat=point_lat, geometry=point_geometry)
  polygon_df = auto2shapely(polygon_df, geometry=polygon_geometry)
  # 空间关联
  df = df.sjoin(
      polygon_df, how='left', predicate=predicate,
  ).drop(['index_right'], axis=1)
  # 统一geometry输出格式、删除geometry、避免多次转换
  if point_geometry in point_df:
    if geometry_format != 'shapely':
      del df[point_geometry]
    if geometry_format == 'shapely' or drop_geometry:
      del point_df[point_geometry]
    else:
      point_df = auto2x(point_df, geometry_format, geometry=point_geometry)
  elif drop_geometry:
    del df[point_geometry]
  else:
    df = shapely2x(df, geometry_format, geometry=point_geometry)
  # 将空间关联后的数据关联到原来的Dataframe上
  return point_df.join(df, how='left')


def nearest_neighbor(
    df: pd.DataFrame,
    df_target: pd.DataFrame,
    c_dst='min_distance',
    epsg: int = None) -> pd.DataFrame:
  """
  近邻分析，计算一个数据集中的元素到另一个数据集中全部元素的最短距离（单位：米）

  Args:
    df:
    df_target:
    c_dst: 输出最短距离的列名，默认为“min_distance”
    epsg: 对于跨时区或不在同一个城市的可以指定epsg code，默认会根据经度中位数获取
  """
  # 将两个数据集都转为shapely格式
  assert df.index.is_unique, 'df索引列必须唯一'
  df_left = _ensure_geometry(df)
  df_target = _ensure_geometry(df_target)
  # 投影
  df_left = projection(df_left, epsg=epsg)
  df_target = projection(df_target, epsg=epsg)
  # 计算最短距离
  df_left = distance_gdf(df_left, df_target, c_dst)
  # 将距离合并到原来的数据集上
  return df.join(df_left[[c_dst]], how='left')


def get_area(
    df: pd.DataFrame,
    c_dst='area',
    epsg: int = None) -> pd.DataFrame:
  """
  计算面积（单位：平方米）
  Args:
    df: 要计算的面数据
    c_dst: 输出面积的列名，默认为“area”
    epsg: 对于跨时区或不在同一个城市的可以指定epsg code，默认会根据经度中位数获取
  """
  # 将数据集转为shapely格式
  assert df.index.is_unique, 'df索引列必须唯一'
  df_left = _ensure_geometry(df)
  # 投影
  df_left = projection(df_left, epsg=epsg)
  # 计算面积
  df_left[c_dst] = df_left.area
  # 将面积合并到原来的数据集上
  return df.join(df_left[[c_dst]], how='left')


def buffer(df: pd.DataFrame,
           radius: Union[int, float],
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
    geo_format: str, 输出的缓冲区geometry格式，支持wkb,wkt,shapely,geojson，默认wkb
  Returns:
    包含缓冲区geometry的DataFrame
  """
  df = df.copy()
  assert df.index.is_unique, 'df索引列必须唯一'
  if geo_type == 'point':
    df_buffer = _ensure_geometry(df, True)
  elif geo_type in ['line', 'polygon']:
    df_buffer = auto2shapely(df, geometry=geometry)[[geometry]]
  else:
    raise ValueError('geo_type必须为point，line或polygon')

  df_buffer = projection(df_buffer, city=city)
  df_buffer[buffer_geometry] = df_buffer.buffer(radius)
  df_buffer = gpd.GeoDataFrame(
      df_buffer[[buffer_geometry]], geometry=buffer_geometry
  )
  df_buffer = projection(df_buffer, epsg=4326, geometry=buffer_geometry)
  df = df.join(df_buffer, how='left')
  return shapely2x(df, geo_format, geometry=buffer_geometry)


def spatial_agg(point_df: pd.DataFrame,
                polygon_df: pd.DataFrame,
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
  Returns:
    pd.DataFrame, 包含空间统计单位字段和被统计字段和面数据geometry的DataFrame
  """

  polygon_df = polygon_df[[by, polygon_geometry]]
  point_df = mark_tags_v2(polygon_df=polygon_df, point_df=point_df,
                          drop_geometry=True, polygon_geometry=polygon_geometry)
  df_grouped = point_df.groupby(by=by, as_index=False).agg(agg)
  return df_grouped


def split_multi_to_rows(df, geometry='geometry', geometry_format=None):
  """将多部件要素拆解为多行的单部件要素"""

  def to_geoms(x):
    if is_empty(x):
      return []
    return [i for i in x.geoms]

  lo = df.shape[0]
  if not geometry_format:
    geometry_format = infer_geom_format(df[geometry])
  df = auto2shapely(df)
  df[geometry] = df[geometry].apply(ensure_multi_geom).apply(to_geoms)
  df = split_list_to_row(df, geometry)
  df = gpd.GeoDataFrame(df, geometry=geometry)
  print(f'Rows: {lo} --> {df.shape[0]}')
  return auto2x(df, geometry_format, geometry)
