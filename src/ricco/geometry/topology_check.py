import logging
import warnings

import geopandas as gpd
import pandas as pd
from pandas.errors import SettingWithCopyWarning
from shapely.geometry import MultiPolygon
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.validation import make_valid

from ..etl.transformer import update_df
from ..util.assertion import assert_not_null
from .util import get_geoms

warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=SettingWithCopyWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

_desc = '''
  拓扑检查
  可检查: 重叠问题, 自相交问题, geometry缺失问题
  可修复: 重叠问题, 自相交问题
'''


def overlap_check(gdf: gpd.GeoDataFrame,
                  geo_col='geometry') -> gpd.GeoDataFrame:
  """
  面数据重叠检查：
  遍历待检查的geoDataFrame, 两两之间检查是否重叠, 并提取重合部分
  """
  overlay_all = []
  for item in range(len(gdf) - 1):
    overlay_one = gpd.overlay(
        gdf.iloc[item: item + 1],
        gdf.iloc[item + 1:],
        how='intersection',
        keep_geom_type=False,
    )
    if not overlay_one.empty:
      overlay_all.append(overlay_one)
  if not overlay_all:
    logging.warning('所有面数据不存在相交情况')
    return gpd.GeoDataFrame()
  return gpd.GeoDataFrame(pd.concat(overlay_all),
                          crs=4326,
                          geometry=geo_col)


def is_contain(r, geo_col='geometry'):
  if r[geo_col].is_empty:
    return False
  diff = r[geo_col].difference(r['geometry_1']
                               .union(r['geometry_2'])
                               .buffer(1e-7, resolution=1))
  if diff.is_empty:
    return True
  else:
    return False


def fix_contains(gdf: gpd.GeoDataFrame,
                 geo_col='geometry',
                 keep_contains=False):
  """
  处理包含关系面数据，只能处理一层包含关系，
  对于多层面数据包含的情况需要多次调用此方法
  Args:
    gdf: 待处理的数据
    geo_col: 数据的geometry列名
    keep_contains: 是否保留被包含的面数据

  Returns:

  """
  df = (
    gdf[[geo_col]]
    .explode(index_parts=True)
    .reset_index(names=['index', 'overlap_index'])
  )
  overlay_all = overlap_check(df, geo_col)
  if overlay_all.empty:
    return 0, gdf

  # 找出被包含的面,会有两种情况：
  # 1.直接被另一个面包含
  # 2.被多个面一起包含
  # 本面与其他面相交情况
  contains_res = (
    overlay_all[['index_1', 'overlap_index_1', 'geometry']]
    .dissolve(by=['index_1', 'overlap_index_1'], as_index=False)
    .rename(columns={'overlap_index_1': 'overlap_index',
                     'index_1': 'index',
                     geo_col: 'geometry_1'})
    .merge(df,
           on=['index', 'overlap_index'],
           how='right')
  )
  # 其他面与本面相交情况
  contains_res = (
    overlay_all
    .dissolve(by=['index_2', 'overlap_index_2'], as_index=False)
    .rename(columns={'overlap_index_2': 'overlap_index',
                     'index_2': 'index',
                     geo_col: 'geometry_2'})
    .merge(contains_res,
           on=['index', 'overlap_index'],
           how='right')
  )
  contains_res = gpd.GeoDataFrame(contains_res,
                                  crs=4326,
                                  geometry=geo_col)
  contains_res['geometry_1'] = contains_res['geometry_1'].fillna(Polygon())
  contains_res['geometry_2'] = contains_res['geometry_2'].fillna(Polygon())
  contains_res['is_contains'] = contains_res.apply(is_contain,
                                                   args=(geo_col,),
                                                   axis=1)
  contains_res = contains_res[
    ['overlap_index', 'index', 'is_contains', geo_col]]
  contains_geo = contains_res[contains_res['is_contains']]
  contains_num = len(contains_geo)
  if not contains_num:
    return 0, gdf
  logging.warning(f'被包含的面有{contains_num}个: %s',
                  contains_geo[['index', geo_col]])
  if keep_contains:
    contains_geo = contains_res[contains_res['is_contains']]
    contains_geo[geo_col] = contains_geo[geo_col].buffer(1e-7)
    fix_contain = contains_res[~contains_res['is_contains']].overlay(
        contains_geo,
        how='difference'
    )
    update_df(contains_res,
              fix_contain,
              on=['index', 'overlap_index'],
              overwrite=True)
  else:
    contains_res.loc[contains_res['is_contains'], geo_col] = Polygon()
  contains_res = contains_res.groupby('index').agg(
      {geo_col: lambda r: unary_union(r.values)})
  res = gdf.drop(geo_col, axis=1).join(contains_res, how='left')
  return contains_num, gpd.GeoDataFrame(res, crs=4326, geometry=geo_col)


def fix_overlap(gdf: gpd.GeoDataFrame,
                geo_col='geometry',
                fill_intersects=False,
                keep_contains=False) -> gpd.GeoDataFrame:
  """
  修复重叠面数据:
  进行重叠检查, 将原始数据和得到重叠部分略微buffer做差集, 以消除重叠部分
  Args:
    gdf: 需要修复的面数据
    geo_col: 面数据geometry列名
    fill_intersects: 是否填满相交的区域，如果为True的话，两个面相交的区域会随机分配到其中一个面内
    keep_contains: fill_intersects为True时才有效，即是否保留被包含的面
  Returns:
    object:

  """
  if not fill_intersects:
    overlay_all = overlap_check(gdf[[geo_col]], geo_col)
    overlay_all[geo_col] = overlay_all[geo_col].buffer(1e-7, resolution=1)
    res = gpd.overlay(gdf[[geo_col]], overlay_all, how='difference')
    gdf_clear = gdf.drop(geo_col, axis=1).join(res, how='left')
    gdf_clear[geo_col] = gdf_clear[geo_col].fillna(Polygon())
    return gpd.GeoDataFrame(gdf_clear, geometry=geo_col, crs=4326)
  else:
    contains_num, gdf_fix_contain = fix_contains(gdf, geo_col, keep_contains)
    # 可能会出现多层包含关系，多次调用方法处理这种情况
    while contains_num:
      contains_num, gdf_fix_contain = fix_contains(gdf_fix_contain,
                                                   geo_col,
                                                   keep_contains)

    df = (
      gdf_fix_contain[[geo_col]]
      .explode(index_parts=True)
      .reset_index(names=['index', 'overlap_index'])
    )
    df['index'] = df['index'].astype('int')
    df = gpd.GeoDataFrame(df, geometry=geo_col, crs=4326, )
    intersects = overlap_check(df, geo_col)
    if intersects.empty:
      return gdf_fix_contain
    intersects = (
      intersects
      .groupby(['overlap_index_1', 'index_1'])
      .agg({geo_col: lambda r: unary_union(r.values)})
      .reset_index()
      .rename(columns={'overlap_index_1': 'overlap_index',
                       'index_1': 'index',
                       geo_col: 'intersects'})
      .merge(df,
             on=['index', 'overlap_index'],
             how='right')
    )

    intersects[geo_col] = intersects.apply(
        lambda r: r[geo_col].difference(
            r['intersects'].buffer(1e-7,
                                   resolution=1))
        if pd.notna(r['intersects'])
        else r[geo_col],
        axis=1)

    res = intersects.groupby('index').agg(
        {geo_col: lambda r: unary_union(r.values)})
    gdf_clear = gdf.drop(geo_col, axis=1).join(res, how='left')
    return gpd.GeoDataFrame(gdf_clear, geometry=geo_col, crs=4326)


def fix_self_intersection(geo: (Polygon, MultiPolygon)) -> MultiPolygon:
  """
  修复自相交面数据，通过调用make_valid方法实现，
  将multipolygon拆分成多个polygon处理，
  对于一个自相交的polygon会保留最大的面
  洞结构也能保留下来
  """
  res = MultiPolygon()
  if not geo.is_valid:
    geoms = get_geoms(geo)
    for g in geoms:
      valid = get_geoms(make_valid(g))
      for v in valid:
        if isinstance(v, Polygon):
          res = res.union(v)
    return res
  return res.union(geo)


def topology_check(gdf: gpd.GeoDataFrame,
                   is_fix=True,
                   geo_col='geometry',
                   fill_intersects=False,
                   keep_contains=False) -> gpd.GeoDataFrame:
  """
  完成全部拓扑检查步骤:
  1. 检查geometry是否有空值并报错
  2. 检查面数据是否自相交并修复
  3. 检查面数据是否重叠并修复
  Args:
    gdf: 要进行拓扑检查的GeoDataFrame
    is_fix: 是否修复
    geo_col: geometry列的列名
    fill_intersects: 是否填满相交的区域，如果为True的话，两个面相交的区域会随机分配到其中一个面内
    keep_contains: fill_intersects为True时才有效，即是否保留被包含的面
  """
  gdf = gdf.copy()
  assert_not_null(gdf, geo_col, skip_if_not_exists=False)
  if gdf.duplicated(geo_col).any():
    raise AssertionError('存在重复的geometry')
  if not all(gdf.is_valid):
    logging.warning('面数据:存在自相交板块,%s', gdf[~gdf.is_valid])
    if is_fix:
      gdf[geo_col] = gdf[geo_col].apply(fix_self_intersection)

  err = overlap_check(gdf)
  if not err.empty:
    logging.warning('面数据:存在重叠板块, %s', err)
    if is_fix:
      gdf = fix_overlap(gdf,
                        geo_col,
                        fill_intersects=fill_intersects,
                        keep_contains=keep_contains)
  return gdf
