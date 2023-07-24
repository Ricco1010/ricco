import logging

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
from shapely.geometry import MultiPolygon
from shapely.geometry import Polygon
from shapely.ops import polygonize
from shapely.ops import unary_union

from .assertion import assert_not_null

_desc = '''
  拓扑检查
  可检查: 重叠问题, 自相交问题, geometry缺失问题
  可修复: 重叠问题, 自相交问题
  已知bug1: 自相交板块有洞结构, 修复自相交时会自动填补缺失洞
  已知bug2: 重叠板块有包含关系时, 被包含的板块会被删除
'''


def overlap_check(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
  """
  面数据重叠检查：
  遍历待检查的geoDataFrame, 两两之间检查是否重叠, 并提取重合部分
  """
  overlay_all = pd.DataFrame()
  for item in range(len(gdf) - 1):
    overlay_one = gpd.overlay(
        gdf.iloc[item: item + 1],
        gdf.iloc[item + 1:],
        how='intersection',
        keep_geom_type=False,
    )
    overlay_all = pd.concat([overlay_all, overlay_one], ignore_index=True)
  overlay_all.crs = gdf.crs
  return overlay_all


def fix_overlap(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
  """
  修复重叠面数据:
  进行重叠检查, 将原始数据和得到重叠部分略微buffer做差集, 以消除重叠部分
  """
  # TODO(maozhixiang): 重叠板块修复时考虑包含和部分包含关系
  overlay_all = overlap_check(gdf)
  overlay_all['geometry'] = overlay_all['geometry'].buffer(1e-7, resolution=1)
  gdf_clear = gpd.overlay(gdf, overlay_all, how='difference')
  gdf_clear.set_geometry(col='geometry', inplace=True)
  gdf_clear.crs = gdf.crs
  return gdf_clear


def fix_self_intersection(one_polygon: (Polygon, MultiPolygon)) -> MultiPolygon:
  """
  修复自相交面数据:
  自相交数据如果是Polygon则将自相交面数据打散, 经纬度坐标重新组合串联,
  拼接成MultiPolygon, 如果是multipolygon则仅保留multipolygon中的最大面,删除小面
  """
  # TODO(maozhixiang): 自相交板块修复时考虑洞结构问题
  if one_polygon.is_valid:
    if isinstance(one_polygon, Polygon):
      x, y = one_polygon.exterior.coords.xy
      list_point = []
      for i in range(len(x.tolist())):
        list_point.append((x[i], y[i]))
      lr = LineString(list_point)
      mls = unary_union(lr)
      one_multipolygon = MultiPolygon(list(polygonize(mls)))
      return one_multipolygon
    elif isinstance(one_polygon, MultiPolygon):
      biggest_polygon = max([j for j in one_polygon], key=lambda x: x.area)
      return biggest_polygon
  return one_polygon


def topology_check(gdf: gpd.GeoDataFrame, is_fix=True) -> gpd.GeoDataFrame:
  """
  完成全部拓扑检查步骤:
  1. 检查geometry是否有空值并报错
  2. 检查面数据是否自相交并修复
  3. 检查面数据是否重叠并修复
  """
  gdf = gdf.copy()
  assert_not_null(gdf, 'geometry', skip_if_not_exists=False)

  if not all(gdf.is_valid):
    logging.warning('面数据:存在自相交板块,%s', gdf[~gdf.is_valid])
    if is_fix:
      gdf['geometry'] = gdf['geometry'].apply(fix_self_intersection)

  err = overlap_check(gdf)
  if not err.empty:
    logging.warning('面数据:存在重叠板块, %s', err)
    if is_fix:
      gdf = fix_overlap(gdf)
  return gdf
