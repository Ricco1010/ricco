import sys
import warnings
from typing import List
from typing import Union

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry

from ..base import agg_parser
from ..base import ensure_list
from ..base import not_empty
from ..base import warn_
from ..etl.transformer import dict2df
from ..etl.transformer import split_list_to_row
from ..util.assertion import assert_not_null
from ..util.assertion import assert_series_unique
from ..util.decorator import process_multi
from ..util.decorator import progress
from ..util.decorator import timer
from ..util.kdtree import kdtree_nearest
from ..util.util import first_notnull_value
from .util import GEOM_FORMATS
from .util import auto_loads
from .util import epsg_from_lnglat
from .util import geojson_dumps
from .util import geojson_loads
from .util import get_epsg
from .util import infer_geom_format
from .util import split_multi_geoms
from .util import wkb_dumps
from .util import wkb_loads
from .util import wkt_dumps
from .util import wkt_loads


def projection(
    df: gpd.GeoDataFrame,
    epsg: int = None,
    city: str = None,
    crs=None,
    c_geometry='geometry'
) -> gpd.GeoDataFrame:
  """
  投影变换

  Args:
    df: 输入的GeomDataFrame格式的数据
    epsg: epsg code, 第一优先级
    city: 城市名称，未传入epsg的情况下将通过城市名称获取epsg，若二者都为空则根据经纬度获取
    crs: 投影坐标系，第二优先级
    c_geometry: geometry的列名
  """
  df = auto2shapely(df, geometry=c_geometry)
  if not epsg and not crs:
    if city:
      epsg = get_epsg(city)
    else:
      df_temp = df.bounds
      lng = df_temp[['minx', 'maxx']].mean(axis=1).median()
      epsg = epsg_from_lnglat(lng)
      print(f'从数据集中自动获取的epsg code为：{epsg}')
  return df.to_crs(epsg=epsg, crs=crs)


@timer()
def projection_lnglat(
    df: pd.DataFrame,
    epsg=None,
    city=None,
    crs=None) -> pd.DataFrame:
  """
  直接对经纬度进行投影变换

  Args:
    df: 输入的GeomDataFrame格式的数据
    epsg: epsg code, 第一优先级
    city: 城市名称，未传入epsg的情况下将通过城市名称获取epsg，若二者都为空则根据经纬度获取
    crs: 投影坐标系，第二优先级
  """
  df = df.copy()
  df_temp = lnglat2shapely(df[['lng', 'lat']])
  df_temp = projection(df_temp, epsg=epsg, city=city, crs=crs)
  df_temp = shapely2lnglat(df_temp[['geometry']])[['lng', 'lat']]
  df.update(df_temp)
  if 'geometry' in df:
    warnings.warn('仅对lng, lat列进行投影变换，未对geometry进行投影变换')
  return df


@progress
def wkb2shapely(df,
                geometry='geometry',
                epsg_code: int = 4326) -> gpd.GeoDataFrame:
  """将wkb格式的geometry列转换为shapely格式"""
  df = df.copy()
  df[geometry] = df[geometry].progress_apply(wkb_loads)
  return gpd.GeoDataFrame(df, geometry=geometry, crs=epsg_code)


@progress
def shapely2wkb(df, geometry='geometry'):
  """将shapely格式的geometry列转换为wkb格式"""
  df = pd.DataFrame(df).copy()
  df[geometry] = df[geometry].progress_apply(wkb_dumps)
  return df


@progress
def wkt2shapely(df,
                geometry='geometry',
                epsg_code: int = 4326) -> gpd.GeoDataFrame:
  """将wkt格式的geometry列转换为shapely格式"""
  df = df.copy()
  df[geometry] = df[geometry].progress_apply(wkt_loads)
  return gpd.GeoDataFrame(df, geometry=geometry, crs=epsg_code)


@progress
def shapely2wkt(df, geometry='geometry'):
  """将shapely格式的geometry列转换为wkt格式"""
  df = pd.DataFrame(df).copy()
  df[geometry] = df[geometry].progress_apply(wkt_dumps)
  return df


@progress
def geojson2shapely(df,
                    geometry='geometry',
                    epsg_code: int = 4326) -> gpd.GeoDataFrame:
  """将geojson格式的geometry列转换为shapely格式"""
  df = df.copy()
  df[geometry] = df[geometry].progress_apply(geojson_loads)
  return gpd.GeoDataFrame(df, geometry=geometry, crs=epsg_code)


@progress
def shapely2geojson(df, geometry='geometry'):
  """将shapely格式的geometry列转换为geojson格式"""
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
  """将经纬度坐标转换为shapely格式的geometry"""
  df = gpd.GeoDataFrame(
      df,
      geometry=gpd.points_from_xy(df[lng], df[lat]),
      crs=epsg_code
  )
  df.rename(columns={'geometry': geometry}, inplace=True)
  df.loc[df[lng].isna() | df[lat].isna(), geometry] = None
  if delete:
    del df[lng], df[lat]
  return gpd.GeoDataFrame(df, geometry=geometry)


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
               delete=False, epsg_code=4326):
  """经纬度转wkb格式的geometry"""
  df = lnglat2shapely(
      df, lng, lat, geometry=geometry, delete=delete, epsg_code=epsg_code
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
               delete=False, epsg_code=4326):
  """经纬度转wkb格式的geometry"""
  df = lnglat2shapely(
      df, lng, lat, geometry=geometry, delete=delete, epsg_code=epsg_code
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
  if geometry in df:
    geom_format = infer_geom_format(df[geometry])
    assert geom_format in GEOM_FORMATS, '未知的地理格式'
    if geom_format == 'shapely':
      return gpd.GeoDataFrame(df, geometry=geometry)
    return getattr(sys.modules[__name__],
                   f'{geom_format}2shapely')(df, geometry=geometry)
  elif 'lng' in df and 'lat' in df:
    warn_('未找到geometry列，尝试将lng/lat列转换为shapely格式')
    return lnglat2shapely(df, delete=False)
  else:
    raise KeyError(f'未找到{geometry}或lng/lat列')


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
  assert geometry_format in GEOM_FORMATS, '未知的地理格式'
  if geometry_format == 'shapely':
    return gpd.GeoDataFrame(df, geometry=geometry)
  return getattr(sys.modules[__name__],
                 f'shapely2{geometry_format}')(df, geometry=geometry)


def auto2x(df, geometry_format: str, geometry='geometry'):
  """
  将geometry转为指定格式

  Args:
    df: 要转换的Dataframe
    geometry_format: 要转换为的geometry类型，支持shapely,wkb,wkt,geojson
    geometry: geometry列的列名，默认为“geometry”
  """
  assert geometry_format in GEOM_FORMATS, '未知的地理格式'
  if infer_geom_format(df[geometry]) == geometry_format:
    return df
  df = auto2shapely(df, geometry=geometry)
  return shapely2x(df, geometry_format=geometry_format, geometry=geometry)


def distance_min(df: gpd.GeoDataFrame, geometry: BaseGeometry) -> float:
  """
  计算数据集df中元素到单个geometry的最短距离

  Args:
    df: 数据集，GeoDataFrame格式
    geometry: 单个geometry，shapely格式
  """
  df = auto2shapely(df)
  geometry = auto_loads(geometry)
  return df.distance(geometry).min()


@process_multi
def distance_gdf(df: gpd.GeoDataFrame, df_target: gpd.GeoDataFrame,
                 c_dst: str = '最小距离',
                 left_geometry='geometry'):
  """计算一个数据集中的每个元素到另一个数据集之间的最短距离"""
  assert df.index.is_unique, 'df 索引列必须唯一'
  df_target = auto2shapely(df_target)
  df_dis = auto2shapely(df[[left_geometry]], geometry=left_geometry)
  df_dis[c_dst] = df_dis[left_geometry].parallel_apply(
      lambda p: distance_min(df_target, p) if not_empty(p) else np.nan
  )
  return df.join(df_dis[[c_dst]])


def split_grids(df: gpd.GeoDataFrame, step: int, geometry_format='wkb'):
  """
  根据所给边界划分固定边长的栅格

  Args:
    df: 边界文件，GeoDataFrame格式
    step: 栅格边长，单位：米
    geometry_format: 栅格格式，支持wkb,wkt,shapely,geojson
  """

  def get_xxyy(_df):
    _df = _df.bounds
    return [
      _df['maxx'][0] - _df['minx'][0], _df['maxy'][0] - _df['miny'][0],
      _df['minx'][0], _df['miny'][0], _df['maxx'][0], _df['maxy'][0]
    ]

  # 融合
  df = auto2shapely(df)
  df = df[['geometry']].dissolve().reset_index(drop=True)
  df.set_crs('epsg:4326', inplace=True)
  # 投影，获取实际的距离
  df_p = projection(df)
  # 分别获取投影前和投影后的点位及边长信息
  xy_o, xy_p = get_xxyy(df), get_xxyy(df_p)
  # 获取栅格的起止经纬度，步长等信息
  xr, yr = xy_o[0] / xy_p[0], xy_o[1] / xy_p[1]
  x_len, y_len = xr * step, yr * step
  x_num, y_num = int(xy_o[0] // x_len + 1), int(xy_o[1] // y_len + 1)
  warn_(f'lng分段数：{x_num}，lat分段数：{y_num}', mode='logging')
  x_start, y_start = xy_o[2], xy_o[3]
  x_end, y_end = x_start + x_num * x_len, y_start + y_num * y_len
  # 构建经纬度列表
  lng_array = np.linspace(x_start, x_end, num=x_num)
  lat_array = np.linspace(y_start, y_end, num=y_num)
  lng_list, lat_list = list(lng_array), list(lat_array)
  # 构建栅格索引
  res = {}
  for i in range(len(lng_list) - 1):
    for j in range(len(lat_list) - 1):
      res[f'{i + 1}-{j + 1}'] = Polygon.from_bounds(
          lng_list[i], lat_list[j], lng_list[i + 1], lat_list[j + 1]
      )
  # 通过边界裁剪栅格
  df_res = gpd.GeoDataFrame(
      dict2df(res, 'grid_id', 'geometry'), crs="epsg:4326")

  df_res = gpd.sjoin(
      df_res, df, how='inner',
      predicate='intersects').drop(
      'index_right', axis=1
  )
  return auto2x(df_res, geometry_format=geometry_format).reset_index(drop=True)


def ensure_geometry(df,
                    ensure_point=False,
                    warning=False,
                    geometry='geometry',
                    lng='lng',
                    lat='lat'):
  """转换并仅保留geometry列"""
  if geometry in df:
    if lng in df and lat in df:
      if not df[df[lng].notna() & df[geometry].isna()].empty:
        warn_(f'存在“{geometry}”为空但经纬度不为空的行', warning)
    df = auto2shapely(df[[geometry]], geometry=geometry)[[geometry]]
    if ensure_point:
      geom = first_notnull_value(df[geometry])
      if geom.geom_type not in ['point', 'Point']:
        warn_('非点数据，提取面内点', warning)
        df = shapely2central_shapely(df, within=True, geometry=geometry)
    return df
  if lng in df and lat in df:
    return lnglat2shapely(
        df[[lng, lat]],
        lng=lng, lat=lat,
        geometry=geometry,
        delete=False,
    )[[geometry]]

  raise KeyError(f'文件中必须有{lng},{lat}列或{geometry}列')


def ensure_lnglat(df, lng='lng', lat='lat', geometry='geometry'):
  """自动提取点或转换为点的经纬度"""
  if lng in df and lat in df:
    return df
  if geometry in df:
    df_temp = auto2shapely(df[[geometry]])
    df_temp = shapely2lnglat(df_temp, within=True)
    return df.join(df_temp[[lng, lat]])
  raise AssertionError('无可转为经纬度的列')


def mark_tags_v2(
    df: pd.DataFrame,
    polygon_df: pd.DataFrame,
    c_tags: (list, str) = None,
    col_list=None,
    *,
    predicate='intersects',
    drop_geometry=False,
    geometry_format='wkb',
    warning=True,
    c_lng='lng',
    c_lat='lat',
    c_geometry='geometry',
    c_polygon_geometry='geometry',
    ensure_point=True
):
  """
  使用面数据通过空间关联（sjoin）给数据打标签

  Args:
    df: 要打标签的数据，一般为点数据，如为面数据，则会自动提取面内点计算
    polygon_df: 标签列所在的数据集，一般为面数据
    c_tags: 面数据中要关联到结果中的标签字段名，若为空则全部关联
    col_list: (已弃用)，同c_tags
    predicate: 关联方法，默认 'intersects'
    drop_geometry: 结果是否删除point_df中的geometry，默认不删除
    geometry_format: 输出的geometry格式，支持wkb,wkt,shapely,geojson，默认wkb
    warning: 是否输出警告信息
    c_lng: 指定点数据的经度列名
    c_lat: 指定点数据的经度列名
    c_geometry: 指定点数据的geometry列名
    c_polygon_geometry: 指定面数据的geometry列名
    ensure_point: point_df是否强制转换为点数据
  """
  if df.empty or polygon_df.empty:
    warn_('存在空的数据集，请检查', warning)
    return df
  if col_list:
    warnings.warn('“col_list”即将弃用，请使用“c_tags”代替', DeprecationWarning)
    c_tags = c_tags or col_list

  df = df.copy()
  assert df.index.is_unique, 'point_df索引列必须唯一'
  if not c_tags:
    c_tags = polygon_df.columns.to_list()
  else:
    c_tags = ensure_list(c_tags)
    polygon_df = polygon_df[[*c_tags, c_polygon_geometry]]

  if cols_mapping := {
    c: f'{c}_origin' for c in c_tags
    if c in df and c not in [c_lng, c_lat, c_geometry]
  }:
    warn_(f'同名字段重命名：{cols_mapping}', warning)
    df.rename(columns=cols_mapping, inplace=True)
  # 检查geometry列是否为空，如果全部为空则不需要进行空间关联
  if c_geometry in df and df[c_geometry].isna().all():
    warn_(f'“{c_geometry}”列全为空，无需进行空间关联')
    for c in c_tags:
      df[c] = None
    return df

  # 转换为shapely格式
  _df = ensure_geometry(df, ensure_point, warning,
                        lng=c_lng, lat=c_lat, geometry=c_geometry)
  polygon_df = auto2shapely(polygon_df, geometry=c_polygon_geometry)
  # 空间关联
  _df = _df.sjoin(
      polygon_df, how='left', predicate=predicate,
  ).drop(['index_right'], axis=1)
  del _df[c_geometry]
  # 统一geometry输出格式、删除geometry、避免多次转换
  if c_geometry in df:
    if drop_geometry:
      del df[c_geometry]
    else:
      df = auto2x(df, geometry_format, geometry=c_geometry)
  # 将空间关联后的数据关联到原来的Dataframe上
  return df.join(_df, how='left')


def nearest_neighbor(
    df: pd.DataFrame,
    df_target: pd.DataFrame,
    c_dst: str = 'min_distance',
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
  df_left = ensure_geometry(df)
  df_target = ensure_geometry(df_target)
  # 投影
  df_left = projection(df_left, epsg=epsg)
  df_target = projection(df_target, epsg=epsg)
  # 计算最短距离
  df_left = distance_gdf(df_left, df_target, c_dst=c_dst)
  # 将距离合并到原来的数据集上
  return df.join(df_left[[c_dst]], how='left')


@progress
def nearest_kdtree(
    df: pd.DataFrame,
    df_poi: pd.DataFrame,
    /, *,
    c_count: str = 'count',
    c_min_distance: str = 'min_distance',
    agg: dict = None,
    limit: int = None,
    r: (int, float) = None,
    keep_origin: bool = False,
    leaf_size: int = 2,
    epsg: int = None,
    city=None,
    crs=None,
):
  """
  KDTree近邻分析，计算一个数据集中的元素到另一个数据集中全部元素的最短距离（单位：米）,
  同时可进行其他运算

  Args:
    df: 基础数据集，统计该数据及周边的其他数据集的信息
    df_poi: 被统计的数据集
    c_count: 计数列字段名，默认“count”
    c_min_distance: 最短距离字段名，默认“min_distance”
    agg: 计算 df_poi 中的其他字段，格式如: {'面积': ['sum', 'mean']}，即计算面积的和、均值
    limit: 限制符合条件的 df_poi 中的个数，由近及远
    r: 限制查询半径
    keep_origin: 是否保留匹配后原始的索引信息
    leaf_size: KDTree 叶子节点大小
    epsg: 投影代码，用于投影，epsg/city/crs指定多个时以epsg为准
    city: 城市，用于获取城市中心点，epsg/city/crs指定多个时以epsg为准
    crs: 数据集的 crs，epsg/city/crs指定多个时以epsg为准
  """
  assert df.index.is_unique and df_poi.index.is_unique, '数据集索引必须唯一'
  # 确保数据中有经纬度
  df_temp = ensure_lnglat(df)
  df_poi = ensure_lnglat(df_poi)

  df_temp = df_temp[df_temp.lng.notna() & df_temp.lat.notna()]
  df_poi = df_poi[df_poi.lng.notna() & df_poi.lat.notna()]
  assert not df_temp.empty and not df_poi.empty, '筛选后数据集为空，请检查经纬度列'
  # 投影
  df_temp = projection_lnglat(
      df_temp, epsg=epsg, city=city, crs=crs
  )[['lng', 'lat']]
  df_poi = projection_lnglat(df_poi, epsg=epsg, city=city, crs=crs)
  # 计算（范围内）的一个点或多个点
  data_tree = df_poi[['lng', 'lat']].values
  data_query = df_temp[['lng', 'lat']].values
  df_temp['ind_list'], df_temp['dist_list'] = kdtree_nearest(
      data_tree, data_query, limit=limit, r=r, leaf_size=leaf_size,
  )
  # 统计数量
  if c_count:
    assert c_count not in df, f'"{c_count}"已存在，请更换列名'
    df_temp[c_count] = df_temp['ind_list'].progress_apply(lambda x: len(x))
  # 计算最短距离
  if c_min_distance:
    assert c_min_distance not in df, f'"{c_min_distance}"已存在，请更换列名'
    df_temp[c_min_distance] = df_temp['dist_list'].progress_apply(
        lambda x: min(x) if len(x) > 0 else None
    )
  # 计算其他字段
  if agg:
    for c_src, func, c_dst in agg_parser(agg):
      df_temp[c_dst] = df_temp['ind_list'].progress_apply(
          lambda x: getattr(df_poi.loc[x][c_src], func)()
      )
  # 保留关联内容
  if not keep_origin:
    del df_temp['ind_list'], df_temp['dist_list']
  del df_temp['lng'], df_temp['lat']
  return df.join(df_temp)


def get_neighbors(
    df: (pd.DataFrame, gpd.GeoDataFrame),
    key_col: str,
    res_type='dict',
) -> (dict, pd.DataFrame):
  """
  获取数据集中每个点的邻居面(相邻标准：至少有一个点相同且不重叠)

  Args:
    df:
    key_col: 关键列，必须唯一
    res_type: 返回类型，可返回dict或Dataframe
  """
  if not key_col:
    key_col = 'index'
    df = df.reset_index()
  assert_series_unique(df, key_col)
  assert_not_null(df, key_col)
  if isinstance(res_type, str):
    res_type = res_type.lower()
  res = {}
  df = auto2shapely(df.copy())
  for key in df[key_col].unique():
    neighbors = []
    v = df[df[key_col] == key].geometry.squeeze()
    for _, row in df.iterrows():
      if v.touches(row['geometry']):
        neighbors.append(row[key_col])
      if neighbors:
        res[key] = neighbors
  if res_type in (dict, 'dict'):
    return res
  if res_type in (pd.DataFrame, 'df', 'dataframe'):
    df = dict2df(res)
    return df.explode('value')
  raise ValueError(f'错误的res_type:{res_type}')


def get_area(
    df: pd.DataFrame,
    c_dst='area',
    epsg: int = None,
    decimals=2) -> pd.DataFrame:
  """
  计算面积（单位：平方米）

  Args:
    df: 要计算的面数据
    c_dst: 输出面积的列名，默认为“area”
    epsg: 对于跨时区或不在同一个城市的可以指定epsg code，默认会根据经度中位数获取
    decimals: 要保留的小数位数
  """
  # 将数据集转为shapely格式
  assert df.index.is_unique, 'df索引列必须唯一'
  assert c_dst not in df, f'"{c_dst}"列已存在，请指定不同的c_dst'
  df_left = ensure_geometry(df)
  # 投影
  df_left = projection(df_left, epsg=epsg)
  # 计算面积
  df_left[c_dst] = df_left.area.round(decimals)
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
    df_buffer = ensure_geometry(df, True)
  elif geo_type in ['line', 'polygon']:
    df_buffer = auto2shapely(df, geometry=geometry)[[geometry]]
  else:
    raise ValueError('geo_type必须为point，line或polygon')
  crs = df_buffer.crs
  df_buffer = projection(df_buffer, city=city)
  df_buffer[buffer_geometry] = df_buffer.buffer(radius)
  df_buffer = gpd.GeoDataFrame(
      df_buffer[[buffer_geometry]], geometry=buffer_geometry
  )
  df_buffer = projection(df_buffer, crs=crs, c_geometry=buffer_geometry)
  df = df.join(df_buffer, how='left')
  return shapely2x(df, geo_format, geometry=buffer_geometry)


def spatial_agg(df: pd.DataFrame,
                polygon_df: pd.DataFrame,
                by: Union[str, List[str]],
                agg: dict,
                c_polygon_geometry: str = 'geometry') -> pd.DataFrame:
  """
  对面数据覆盖范围内的点数据进行空间统计

  Args:
    df: 点数据dataframe;
    polygon_df: 面数据dataframe;
    by: 空间统计单位字段；
    agg: 空间统计操作。格式为{'被统计字段名': '操作名', ...}的字典。如{'poi':'sum'};
    c_polygon_geometry: 面数据geometry字段名，默认"geometry";
  Returns:
    pd.DataFrame, 包含空间统计单位字段和被统计字段和面数据geometry的DataFrame
  """

  polygon_df = polygon_df[[by, c_polygon_geometry]]
  df = mark_tags_v2(
      df=df,
      polygon_df=polygon_df,
      c_tags=by,
      drop_geometry=True,
      c_polygon_geometry=c_polygon_geometry)
  df_grouped = df.groupby(by=by, as_index=False).agg(agg)
  return df_grouped


def split_multi_to_rows(df, geometry='geometry', geometry_format=None):
  """将多部件要素拆解为多行的单部件要素"""

  lo = df.shape[0]
  if not geometry_format:
    geometry_format = infer_geom_format(df[geometry])
  df = auto2shapely(df)
  df[geometry] = df[geometry].apply(split_multi_geoms)
  df = split_list_to_row(df, geometry)
  df = gpd.GeoDataFrame(df, geometry=geometry)
  print(f'Rows: {lo} -> {df.shape[0]}')
  return auto2x(df, geometry_format, geometry)
