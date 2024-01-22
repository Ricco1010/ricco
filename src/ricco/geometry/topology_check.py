import warnings

import geopandas as gpd
import pandas as pd
from shapely.errors import ShapelyDeprecationWarning
from shapely.geometry import GeometryCollection
from shapely.geometry import MultiPolygon
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.validation import make_valid
from tqdm import tqdm

from .df import auto2shapely

warnings.filterwarnings('ignore', category=ShapelyDeprecationWarning)

_desc = '''
  拓扑检查
  可检查: 重叠问题, 自相交问题, geometry缺失问题
  可修复: 重叠问题, 自相交问题
'''


def topology_check(gdf: gpd.GeoDataFrame, geo_col='geometry'):
  """
  判断整列geometry是否规范, 仅支持面数据，
  检查geometry是否有空值，
  检查每个geometry是否存在拓扑问题，
  检查整列geometry之间是否存在拓扑问题

  Args:
    gdf: 需要进行拓扑修复的GeoDataFrame
    geo_col: geometry列列名

  Returns:
    geometry数据是否规范
  """
  gdf = auto2shapely(gdf, geometry=geo_col)
  geo_data = gdf[geo_col]
  if len(geo_data[geo_data.isnull()]):
    raise ValueError('存在空数据')
  if not all([isinstance(geo, (Polygon, MultiPolygon)) for geo in geo_data]):
    raise ValueError('存在非面类型的地理数据')
  for index, geo in tqdm(geo_data.items(),
                         desc='topology_check',
                         total=len(geo_data)):
    if not geo.is_valid:
      return False
    for i, g in geo_data.items():
      if i == index:
        continue
      if geo.intersects(g):
        return False
  return True


def fix_polygon_topology(gdf: gpd.GeoDataFrame,
                         geo_col='geometry',
                         fill_intersects=False,
                         keep_contains=False) -> gpd.GeoDataFrame:
  """
  修复面地理数据的拓扑问题,index不能重复

  Args:
    gdf: 需要进行拓扑修复的GeoDataFrame
    geo_col: geometry列列名
    fill_intersects: 是否填满相交的区域，如果为True的话，两个面相交的区域会随机分配到其中一个面内
    keep_contains: fill_intersects为True时才有效，即是否强制保留被包含的面

  Returns:
    修复完拓扑问题的GeoDataFrame
  """
  gdf = auto2shapely(gdf, geometry=geo_col)
  if topology_check(gdf, geo_col):
    return gdf
  gdf[geo_col] = series_geometry_fix_topology(gdf[geo_col],
                                              fill_intersects,
                                              keep_contains)
  return gpd.GeoDataFrame(gdf, crs=4326, geometry=geo_col)


def series_geometry_fix_topology(series: pd.Series,
                                 fill_intersects=True,
                                 keep_contains=True):
  """
  Args:
    series: series的index不能重复, 如果keep_contains=True,geometry不能相互包含
    fill_intersects: 是否填满相交的区域，如果为True的话，两个面相交的区域会分配到更靠后的面内
    keep_contains: fill_intersects为True时才有效，即是否强制保留被包含的面
  """
  if any(series.index.duplicated()):
    raise ValueError('duplicated index')

  def fix_valid(x):
    if not x.is_valid:
      valid_res = make_valid(x)
      if isinstance(valid_res, GeometryCollection):
        return unary_union([i for i in valid_res.geoms if
                            isinstance(i, (Polygon, MultiPolygon))])
      return valid_res
    return x

  series = series.apply(fix_valid)

  def ser_intersect(geo_ser: series):
    intersect_info = dict()
    for index, geo in tqdm(geo_ser.items(),
                           desc='get_intersects_info',
                           total=len(geo_ser)):
      intersect_list = []
      intersect_polygon = MultiPolygon()
      for i, g in geo_ser.items():
        if i == index:
          continue
        # TODO(fanjianbang) rtree优化
        if geo.intersects(g):
          intersect_list.append(i)
          intersect_polygon = intersect_polygon.union(g)
      intersect_info[index] = {}
      intersect_info[index]['intersect_list'] = intersect_list
      intersect_info[index]['is_contains'] = intersect_polygon.contains(geo)
    return intersect_info

  def fix_intersects(geo_ser: series):
    intersect_info = ser_intersect(geo_ser)
    res_geo = []
    res_index = []
    contains_geo = []
    contains_index = []
    for index, geo in tqdm(geo_ser.items(),
                           desc='fix_intersects',
                           total=len(geo_ser)):
      info = intersect_info.get(index)
      intersect_list = info.get('intersect_list')
      if info.get('is_contains') and fill_intersects and keep_contains:
        contains_geo.append(geo)
        contains_index.append(index)
      else:
        for i in intersect_list:
          if fill_intersects and i in res_index:
            continue
          geo = geo.difference(geo_ser.loc[i].buffer(1e-7))
        if isinstance(geo, GeometryCollection):
          geo = unary_union(
              [i for i in geo.geoms if isinstance(i, (Polygon, MultiPolygon))])
        res_geo.append(geo)
        res_index.append(index)
    intersect_res = pd.Series(res_geo, index=res_index)
    if contains_index:
      if set(contains_index) == set(geo_ser.index):
        raise ValueError('mutual inclusion geometry')
      contains_res = fix_intersects(pd.Series(contains_geo,
                                              index=contains_index))
      return pd.concat([intersect_res, contains_res])
    else:
      return intersect_res

  res = fix_intersects(series)
  return res
