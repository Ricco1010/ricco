import csv
import json
import logging
import os
import sys
from tempfile import NamedTemporaryFile

import geopandas as gpd
import pandas as pd
from tqdm import tqdm

from ..base import ensure_list
from ..fs.oss import OssUtils
from ..geometry.util import wkt_loads
from ..util.os import dir_iter
from ..util.os import extension
from ..util.os import path_name
from . import ALL_EXTS


def _df_desc(df):
  """数据集基本信息打印"""
  print(f'shape: {df.shape}')
  print(f'columns: {df.columns.tolist()}')
  return df


def rdf(
    file_path: str,
    *,
    sheet_name=0,
    sheet_contains: str = None,
    encoding: str = None,
    info: bool = False,
    dtype=None,
    columns: (list, str) = None,
    nrows: int = None,
    recursive: bool = True,
    access_key=None,
    secret_key=None,
) -> pd.DataFrame:
  """
  常用文件读取函数，支持
  .csv/.xlsx/.xls/.shp/.parquet/.pickle/.feather/.kml/.ovkml/
  .geojson/.shp/.json等

  Args:
    file_path: 文件或文件夹路径
    sheet_name: 数据所在sheet的名称，仅对.xlsx/.xls生效
    sheet_contains: 筛选sheet名称中包含此字符串的sheet，仅对.xlsx/.xls生效
    encoding: 编码
    info: 是否打印数据集情况（shape & columns）
    dtype: 指定读取列的类型
    columns: 指定读取的列名
    nrows: 指定读取的行数
    recursive: 是否循环遍历更深层级的文件夹，默认为True，仅当路径为文件夹时生效
    access_key: 阿里云OSS访问密钥
    secret_key: 阿里云OSS访问密钥
  """
  if file_path.startswith('oss://'):
    assert access_key and secret_key, 'access_key和secret_key不能为空'
    return read_oss(file_path, access_key, secret_key, columns, nrows, encoding)

  if os.path.isdir(file_path):
    if file_path.endswith('.gdb'):
      return read_gdb(file_path)
    # 此部分为递归，注意避免无限递归
    return rdf_by_dir(file_path, columns=columns, info=info,
                      recursive=recursive, encoding=encoding)

  if columns:
    columns = ensure_list(columns)

  ex = extension(file_path)
  assert ex in ALL_EXTS, f'未知的文件扩展名：{ex}'

  if ex == '.csv':
    df = read_csv(
        file_path, dtype=dtype, columns=columns, nrows=nrows, encoding=encoding)
  if ex in ('.xls', '.xlsx'):
    df = rdxls(
        file_path, sheet_name=sheet_name, sheet_contains=sheet_contains,
        dtype=dtype, columns=columns, nrows=nrows)
  if ex in ('.shp', '.dbf', '.shx', '.geojson'):
    df = read_shapefile(file_path, encoding=encoding, nrows=nrows)
  if ex in ('.pa', '.parquet'):
    df = pd.read_parquet(file_path, columns=columns)
  if ex == '.feather':
    df = pd.read_feather(file_path, columns=columns)
  if ex == '.pickle':
    df = pd.read_pickle(file_path)
  if ex == '.json':
    df = pd.read_json(file_path, encoding=encoding, nrows=nrows, dtype=dtype)
  if ex in ('.kml', '.ovkml'):
    df = read_kml(file_path)
  if ex in ('.sav', '.zsav'):
    df = read_spss(file_path, encoding=encoding, columns=columns, nrows=nrows)

  df = df[columns] if columns else df  # noqa
  df = df.head(nrows) if nrows else df
  return _df_desc(df) if info else df


def _max_grid():
  """防止单个单元格文件过大而报错"""
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
    *,
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


def read_all_sheets(file_path, sheet_names=None, ignore_diff_columns=False):
  """
  读取并合并所有sheet表

  Args:
    file_path: Excel文件路径
    sheet_names: 要读取并合并的sheet列表，默认读取全部的sheet
    ignore_diff_columns: 如果每个sheet中的字段名不一致，是否要忽略
  """
  assert extension(file_path) in ('.xlsx', '.xls'), '必须是Excel文件'
  data = pd.read_excel(file_path, sheet_name=None)
  if not sheet_names:
    sheet_names = list(data.keys())
  dfs = []
  columns = set(data[sheet_names[0]].columns)
  for sheet_name in sheet_names:
    _df = data[sheet_name]
    assert 'sheet_name' not in _df
    if not ignore_diff_columns:
      assert set(_df.columns) == columns, f'sheet: "{sheet_name}", 列名不一致'
    _df['sheet_name'] = sheet_name
    dfs.append(_df)
  return pd.concat(dfs, ignore_index=True)


def read_csv(file_path: str,
             *,
             encoding: str = None,
             dtype=None,
             columns: (list, str) = None,
             nrows: int = None,
             **kwargs):
  """读取csv文件，基于 `pd.read_csv`，加入编码尝试"""
  _max_grid()
  encodings = [encoding] if encoding else ['utf-8', 'gbk', 'utf-8-sig']
  for encode in encodings:
    try:
      return pd.read_csv(
          file_path, engine='python', dtype=dtype, usecols=columns,
          nrows=nrows, encoding=encode, **kwargs)
    except UnicodeDecodeError:
      pass
  raise Exception(f'使用encoding{encodings}均无法读取文件，请指定')


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


def rdf_by_dir(
    dir_path, exts=None, ignore_index=True, recursive=False,
    columns: (list, str) = None, info=False,
    sign_data_from: bool = False, col_data_from: str = '__data_from',
    encoding: str = None
) -> pd.DataFrame:
  """
  从文件夹中读取所有文件并拼接成一个DataFrame

  Args:
    dir_path: 文件夹路径
    exts: 要读取的文件扩展名
    ignore_index: 是否忽略索引
    recursive: 是否循环遍历更深层级的文件夹
    columns: 指定列名
    info: 是否打印基本信息（列名、行列数）
    sign_data_from: 是否标记数据来源于哪个文件，默认不标记
    col_data_from: 用于标记数据来源文件的列名
    encoding: 文件编码，默认为utf-8
  """
  desc = dir_path if len(dir_path) <= 23 else f'...{dir_path[-20:]}'
  path_list = []
  for p in dir_iter(dir_path, exts=exts or ALL_EXTS, ignore_hidden_files=True,
                    recursive=recursive):
    path_list.append(p)
  dfs = []
  for filename in tqdm(path_list, desc=desc):
    assert os.path.isfile(filename), f'{filename} is not a file'
    _df = rdf(filename, columns=columns, encoding=encoding)
    if sign_data_from:
      if col_data_from in _df:
        raise KeyError(
            f'{col_data_from}列名已被占用， 请指定其他的`col_data_from`')
      _df[col_data_from] = filename
    dfs.append(_df.copy())
  df = pd.concat(dfs, ignore_index=ignore_index)
  return _df_desc(df) if info else df


def kml_df_create_level(gdf_dict: dict) -> dict:
  """
  读取 dict {level: gpd.GeoDataFrame} 字典, 并根据[name]列包含关系提取分辨文件夹层级

  Args:
    gdf_dict: {dict} {level: gpd.GeoDataFrame} key为文件夹名称, value为对应数据
  Returns:
    文件夹层级字典，如:{'板块名称': 0, 'T顶豪': 1, 'O1远郊品质': 2}
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


def get_kml_df_with_level(gdf_dict: dict) -> gpd.GeoDataFrame:
  """
  从中gdf_dict读取数据以及文件夹名称,并构造文件夹层级,按照指定层级合并所
  有数据,并打上层级标签

  Args:
    gdf_dict: GeoDataFrame组成的字典，key为文件夹名称, value为对应数据：{level: gpd.GeoDataFrame}
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


def read_shapefile_with_driver(file_path, encoding='utf-8') -> gpd.GeoDataFrame:
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


def read_shapefile(file_path, **kwargs):
  """读取shapefile或geojson文件"""
  encoding = kwargs.get('encoding', 'utf-8')
  nrows = kwargs.get('nrows', None)
  try:
    df = gpd.GeoDataFrame.from_file(file_path, encoding=encoding, rows=nrows)
  except ValueError as e:
    if extension(file_path) != '.geojson':
      logging.warning(f'常规读取方式读取失败，尝试其他方式读取，{e}')
      df = read_shapefile_with_driver(file_path, encoding=encoding)
    else:
      raise ValueError(f'文件读取失败，{e}')
  finally:
    logging.warning(f'请检查输出结果并指定正确的encoding，当前为"{encoding}"')
  return df


def read_gdb(dir_path):
  """读取gdb文件夹"""
  return gpd.read_file(
      dir_path,
      driver='FileGDB',
  )


def read_spss(file_path, columns=None, nrows=None, encoding=None):
  """读取SPSS的.sav文件"""
  import pyreadstat
  df, meta = pyreadstat.read_sav(
      file_path,
      usecols=columns,
      row_limit=nrows or 0,
      encoding=encoding)
  return pd.DataFrame(df, columns=meta.column_names)


def read_oss(file_path, access_key, secret_key, columns=None, nrows=None,
             encoding=None):
  """读取OSS文件"""
  assert file_path.startswith('oss://'), '文件路径必须以oss://开头'
  work_path = path_name(file_path)
  ext = extension(file_path)
  _oss = OssUtils(
      work_path=work_path,
      access_key=access_key,
      secret_key=secret_key
  )
  with NamedTemporaryFile(suffix=ext) as _temp:
    _oss.download(file_path, _temp.name, overwrite=True)
    df = rdf(_temp.name, encoding=encoding, nrows=nrows, columns=columns)
  return df
