import csv
import json
import warnings

import geopandas as gpd
import pandas as pd
from tqdm import tqdm

from ..geometry.util import wkt_loads
from ..util.base import ensure_list
from ..util.exception import UnknownFileTypeError
from ..util.os import dir_iter
from ..util.os import extension
from ..util.os import path_name


def max_grid():
  """防止单个单元格文件过大而报错"""
  import sys
  maxint = sys.maxsize
  decrement = True
  while decrement:
    decrement = False
    try:
      csv.field_size_limit(maxint)
    except OverflowError:
      maxint = int(maxint / 10)
      decrement = True


def rdxls(
    file_path,
    sheet_name=0,
    sheet_contains: str = None,
    dtype=None,
    columns: (list, str) = None,
    nrows: int = None
) -> pd.DataFrame:
  """
  读取excel文件
  Args:
    file_path: 文件名
    sheet_name: sheet表的名称
    sheet_contains: sheet表包含的字符串
    dtype: 指定读取列的类型
    columns: 指定读取的列
    nrows: 指定读取的行数
  """
  if sheet_contains:
    assert not sheet_name, 'sheet_name和sheet_contains不能同时指定'
    dataset = pd.read_excel(file_path, sheet_name=None, dtype=dtype,
                            usecols=columns, nrows=1)
    sheets = [i for i in dataset if sheet_contains in i]
    assert len(sheets) == 1, f'0个或多个sheet包含{sheet_contains}'
    sheet_name = sheets[0]
    print(f'通关关键字"{sheet_contains}"匹配到唯一的sheet_name"{sheet_name}"')
  return pd.read_excel(
      file_path, sheet_name=sheet_name, dtype=dtype, usecols=columns,
      nrows=nrows)


def rdf(
    file_path: str,
    *,
    sheet_name=0,
    sheet_contains: str = None,
    encoding: str = 'utf-8-sig',
    info: bool = False,
    dtype=None,
    columns: (list, str) = None,
    nrows: int = None,
) -> pd.DataFrame:
  """
  常用文件读取函数，支持.csv/.xlsx/.xls/.shp/.parquet/.pickle/.feather/.kml/.ovkml'
  Args:
    file_path: 文件路径
    sheet_name: 数据所在sheet的名称，仅对.xlsx/.xls生效
    sheet_contains: 筛选sheet名称中包含此字符串的sheet，仅对.xlsx/.xls生效
    encoding: 编码
    info: 是否打印数据集情况（shape & columns）
    dtype: 指定读取列的类型
    columns: 指定读取的列名
    nrows: 指定读取的行数
  """
  max_grid()
  if columns:
    columns = ensure_list(columns)
  ex = extension(file_path)
  if ex == '.csv':
    try:
      df = pd.read_csv(
          file_path, engine='python', dtype=dtype, usecols=columns, nrows=nrows,
          encoding=encoding)
    except UnicodeDecodeError:
      df = pd.read_csv(
          file_path, engine='python', dtype=dtype, usecols=columns, nrows=nrows)
  elif ex == '.feather':
    df = pd.read_feather(file_path, columns=columns)
  elif ex == '.parquet':
    df = pd.read_parquet(file_path, columns=columns)
  elif ex == '.pickle':
    df = pd.read_pickle(file_path)
  elif ex in ('.xls', '.xlsx'):
    df = rdxls(
        file_path, sheet_name=sheet_name, sheet_contains=sheet_contains,
        dtype=dtype, columns=columns, nrows=nrows
    )
  elif ex == '.shp':
    try:
      df = gpd.GeoDataFrame.from_file(file_path, encoding=encoding, rows=nrows)
    except ValueError as e:
      warnings.warn(f'常规读取方式读取失败，尝试其他方式读取，{e}')
      df = read_shapefile(file_path, encoding=encoding)
    finally:
      warnings.warn(f'请检查输出结果并指定正确的encoding，当前为"{encoding}"')
  elif ex in ('.kml', '.ovkml'):
    df = read_kml(file_path)
  elif ex == '.json':
    df = read_line_json(file_path, encoding=encoding)
  else:
    raise UnknownFileTypeError('未知文件格式')
  df = df[columns] if columns else df
  df = df.head(nrows) if nrows else df
  if info:
    print(f'shape: {df.shape}')
    print(f'columns: {df.columns.tolist()}')
  return df


def read_line_json(file_path, encoding='utf-8') -> pd.DataFrame:
  """
  逐行读取json格式的文件
  Args:
    file_path: 文件名
    encoding: 文件编码，默认为utf-8
  """
  records = []
  with open(file_path, 'r', encoding=encoding) as file:
    for line in file:
      row = json.loads(line)
      records.append(row)
  return pd.DataFrame(records)


def rdf_by_dir(dir_path, exts=None, ignore_index=True, recursive=False,
               columns: (list, str) = None, info=False) -> pd.DataFrame:
  """
  从文件夹中读取所有文件并拼接成一个DataFrame
  Args:
    dir_path: 文件夹路径
    exts: 要读取的文件扩展名
    ignore_index: 是否忽略索引
    recursive: 是否循环遍历更深层级的文件夹
    columns: 指定列名
    info: 是否打印基本信息（列名、行列数）
  """
  desc = dir_path if len(dir_path) <= 23 else f'...{dir_path[-20:]}'
  path_list = []
  for p in dir_iter(dir_path, exts=exts, ignore_hidden_files=True,
                    recursive=recursive):
    path_list.append(p)
  dfs = []
  for filename in tqdm(path_list, desc=desc):
    dfs.append(rdf(filename, columns=columns))
  df = pd.concat(dfs, ignore_index=ignore_index)
  if info:
    print(f'shape: {df.shape}')
    print(f'columns: {df.columns.tolist()}')
  return df


def read_parquet_by_dir(dir_path, ignore_index=True) -> pd.DataFrame:
  """从文件夹中读取所有的parquet文件并拼接成一个DataFrame"""
  return rdf_by_dir(dir_path, exts=['.parquet'], ignore_index=ignore_index)


def kml_df_create_level(gdf_dict) -> dict:
  """
  读取 dict {level: gpd.GeoDataFrame} 字典, 并根据[name]列包含关系提取
  分辨文件夹层级
  Args:
    gdf_dict: {dict} {level: gpd.GeoDataFrame} key为文件夹名称, value为对应数据
  Returns: dict: 文件夹层级字典
      example:
        {'板块名称': 0,
        'T顶豪': 1,
        'TOP1城区顶级': 2,
        'O远郊': 1,
        'O1远郊品质': 2,
        'O2远郊安居': 2}
  """
  level_dict = {}
  for i in gdf_dict:
    level_dict[i] = 0
  for k in range(1, len(gdf_dict)):
    for j in list(gdf_dict.keys())[k:]:
      sample = list(gdf_dict.keys())[k - 1]
      if set(gdf_dict[j]['name']) <= set(gdf_dict[sample]['name']):
        level_dict[j] = level_dict[sample] + 1
  return level_dict


def get_kml_df_with_level(gdf_dict) -> gpd.GeoDataFrame:
  """
  从中gdf_dict读取数据以及文件夹名称,并构造文件夹层级,按照指定层级合并所
  有数据,并打上层级标签
  Args:
    gdf_dict{dict}:{level: gpd.GeoDataFrame} key为文件夹名称, value为对应数据
  """
  level_dict = kml_df_create_level(gdf_dict)
  level_dict_new = {}
  for k, v in level_dict.items():
    columns_name = f'level_{v}'
    if columns_name not in level_dict_new:
      level_dict_new[columns_name] = []
    gdf_dict[k][columns_name] = k
    level_dict_new[columns_name].append(gdf_dict[k])
  data_all = gpd.GeoDataFrame(columns=['name', 'geometry'])
  for v in level_dict_new.values():
    level_df = pd.concat(v)
    data_all = data_all.merge(level_df, on=['name', 'geometry'], how='outer')
  data_all['name'] = data_all['name'].replace('-', None)
  return data_all


def read_kml(file_path, keep_level=True) -> gpd.GeoDataFrame:
  """
  读取kml类文件,将其转换成DataFrame, 根据separate_folders选择是否拆分,
  输出仅保留[name, geometry]字段,暂时只支持polygon和multipolygon数据
  Args:
    file_path: kml or ovkml文件路径
    keep_level: 是否保留文件夹层级标签
  """
  import kml2geojson as k2g
  features = k2g.convert(file_path, separate_folders=keep_level)
  gdf_dict = {}
  if keep_level:
    for i in range(len(features)):
      gdf = gpd.GeoDataFrame.from_features(features[i]['features'])
      level = features[i]['name']
      if 'name' not in gdf.columns:
        gdf['name'] = '-'
      gdf = gdf[['name', 'geometry']]
      gdf_dict[level] = gdf
    data_all = get_kml_df_with_level(gdf_dict)
  else:
    data_all = gpd.GeoDataFrame.from_features(features[0]['features'])
    data_all = data_all[['name', 'geometry']]
  return data_all


def read_shapefile(file_path, encoding='utf-8') -> gpd.GeoDataFrame:
  """读取shapefile文件，分别读取dbf中的属性表和shp中的geometry进行拼接"""
  from osgeo import ogr
  from simpledbf import Dbf5

  filename = path_name(file_path)
  # 读取.dbf文件
  df = Dbf5(f'{filename}.dbf', codec=encoding).to_dataframe()
  df = gpd.GeoDataFrame(df)
  # 读取并转换shp文件中的geometry
  geoms = []
  driver = ogr.GetDriverByName('ESRI Shapefile')
  data_source = driver.Open(f'{filename}.shp', 0)  # 0表示只读模式
  layer = data_source.GetLayer()
  for i, feature in enumerate(layer):
    geom_wkt = feature.GetGeometryRef().ExportToWkt()
    geoms.append(wkt_loads(geom_wkt))
  df['geometry'] = geoms
  return gpd.GeoDataFrame(df)
