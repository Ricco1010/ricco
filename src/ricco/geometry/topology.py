import warnings
from itertools import combinations

import geopandas as gpd
import pandas as pd
from shapely.errors import ShapelyDeprecationWarning
from shapely.geometry import MultiPolygon
from tqdm import tqdm

from ..util.assertion import assert_not_null
from ..util.assertion import assert_subset
from .df import auto2shapely
from .util import ensure_valid_polygon
from .util import filter_polygon_from_collection

warnings.filterwarnings('ignore', category=ShapelyDeprecationWarning)

_desc = '''
  拓扑检查
  可检查: 重叠问题, 自相交问题, geometry缺失问题
  可修复: 重叠问题, 自相交问题
'''


def is_topology_valid(df: gpd.GeoDataFrame, c_geometry='geometry'):
  """
  判断整列geometry是否规范, 仅支持面数据，
    * 检查geometry是否有空值，
    * 检查每个geometry是否存在拓扑问题，
    * 检查整列geometry之间是否存在拓扑问题

  Args:
    df: 需要进行拓扑修复的GeoDataFrame
    c_geometry: geometry列名

  Returns:
    geometry数据是否规范
  """
  df = auto2shapely(df, geometry=c_geometry)
  assert_not_null(df, c_geometry)
  assert_subset(df.geom_type.unique(), {'Polygon', 'MultiPolygon'})

  if not all(df.is_valid):
    return False

  n = df.shape[0]
  for x, y in tqdm(combinations(df.geometry, 2), total=n * (n - 1) / 2,
                   desc='topology check'):
    if x.intersects(y):
      return False
  return True


def _fix_topology(series: pd.Series,
                  fill_intersects=True,
                  keep_contains=True):
  """
  Args:
    series: series的index不能重复, 如果keep_contains=True,geometry不能相互包含
    fill_intersects: 是否填满相交的区域，如果为True的话，两个面相交的区域会分配到更靠后的面内
    keep_contains: fill_intersects为True时才有效，即是否强制保留被包含的面
  """

  def ser_intersect(geo_ser: pd.Series):
    intersect_info = {index: {'intersect_list': [], 'is_contains': False}
                      for index in geo_ser.index}
    size = geo_ser.shape[0]
    for index_x, index_y in tqdm(combinations(geo_ser.index, 2),
                                 total=size * (size - 1) / 2,
                                 desc='intersect info'):
      geo_x = geo_ser.loc[index_x]
      geo_y = geo_ser.loc[index_y]
      if geo_x.intersects(geo_y):
        intersect_info[index_x]['intersect_list'].append(index_y)
        intersect_info[index_y]['intersect_list'].append(index_x)

    for index, info in tqdm(intersect_info.items(),
                            total=len(intersect_info.keys()),
                            desc='contains info'):
      intersect_list = info['intersect_list']
      polygon = MultiPolygon()
      for i in intersect_list:
        polygon = polygon.union(series.loc[i])
      intersect_info[index]['is_contains'] = polygon.contains(series.loc[index])
    return intersect_info

  def fix_intersects(geo_ser: pd.Series):
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
      if info.get('is_contains') and keep_contains:
        contains_geo.append(geo)
        contains_index.append(index)
      else:
        for i in intersect_list:
          if fill_intersects and i in res_index:
            continue
          geo = geo.difference(geo_ser.loc[i].buffer(1e-7))
        res_geo.append(filter_polygon_from_collection(geo))
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

  assert series.is_unique, 'duplicated index'
  series = series.apply(ensure_valid_polygon)
  res = fix_intersects(series)
  return res


def fix_topology(df: gpd.GeoDataFrame,
                 c_geometry='geometry',
                 fill_intersects=False,
                 keep_contains=False) -> gpd.GeoDataFrame:
  """
  修复面地理数据的拓扑问题,index不能重复

  Args:
    df: 需要进行拓扑修复的GeoDataFrame
    c_geometry: geometry列列名
    fill_intersects: 是否填满相交的区域，如果为True的话，两个面相交的区域会随机分配到其中一个面内
    keep_contains: fill_intersects为True时才有效，即是否强制保留被包含的面

  Returns:
    修复完拓扑问题的GeoDataFrame
  """
  df = auto2shapely(df, geometry=c_geometry)
  if is_topology_valid(df, c_geometry):
    return df
  df[c_geometry] = _fix_topology(df[c_geometry],
                                 fill_intersects,
                                 keep_contains)
  return gpd.GeoDataFrame(df, crs=4326, geometry=c_geometry)
