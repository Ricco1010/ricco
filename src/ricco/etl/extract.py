import csv
import warnings

import geopandas as gpd
import pandas as pd
from tqdm import tqdm

from ..util.os import dir_iter
from ..util.os import extension
from ..util.util import ensure_list


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
    filename,
    sheet_name=0,
    sheet_contains: str = None,
    errors='raise',
    dtype=None,
    columns=None,
) -> pd.DataFrame:
  """
  读取excel文件
  Args
    filename: 文件名
    sheet_name: sheet表的名称
    sheet_contains: sheet表包含的字符串
    errors: 当没有对应sheet时，raise: 抛出错误, coerce: 返回空的dataframe
    dtype: 指定读取列的类型
  """
  assert errors in ('coerce', 'raise'), '可选参数为coerce和raise'
  if sheet_name == 0:
    if sheet_contains is not None:
      df = pd.read_excel(filename, sheet_name=None, dtype=dtype,
                         usecols=columns)
      sheet_list = [i for i in df.keys() if sheet_contains in i]
      if len(sheet_list) != 0:
        sheet_name = sheet_list[0]
        if len(sheet_list) == 1:
          print(f"sheet:  <'{sheet_name}'>")
        elif len(sheet_list) >= 2:
          warnings.warn(
              f"包含'{sheet_contains}'的sheet有{sheet_list}，所读取的sheet为:{sheet_name}")
        return df[sheet_name]
      else:
        if errors == 'coerce':
          warnings.warn(f'没有包含{sheet_contains}的sheet，请检查')
          return pd.DataFrame()
        else:
          raise ValueError(f'没有包含{sheet_contains}的sheet，请检查')
  else:
    print(f"sheet:  <'{sheet_name}'>")
  return pd.read_excel(filename, sheet_name=sheet_name, dtype=dtype,
                       usecols=columns)


def rdf(
    file_path: str,
    *,
    sheet_name=0,
    sheet_contains: str = None,
    encoding: str = 'utf-8-sig',
    info: bool = False,
    dtype=None,
    columns: list = None,
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
  """
  max_grid()
  if columns:
    columns = ensure_list(columns)
  ex = extension(file_path)
  if ex == '.csv':
    try:
      df = pd.read_csv(
          file_path, engine='python', encoding=encoding,
          dtype=dtype, usecols=columns,
      )
    except UnicodeDecodeError:
      df = pd.read_csv(file_path, engine='python', dtype=dtype, usecols=columns)
  elif ex in ('.parquet', '.feather'):
    _t = ex.strip('.')
    df = getattr(pd, f'read_{_t}')(file_path, columns=columns)
  elif ex == '.pickle':
    df = pd.read_pickle(file_path)
  elif ex in ('.xls', '.xlsx'):
    df = rdxls(
        file_path, sheet_name=sheet_name, sheet_contains=sheet_contains,
        dtype=dtype, columns=columns
    )
  elif ex == '.shp':
    try:
      df = gpd.GeoDataFrame.from_file(file_path)
    except UnicodeEncodeError:
      df = gpd.GeoDataFrame.from_file(file_path, encoding='GBK')
  elif ex in ('.kml', '.ovkml'):
    df = read_kml(file_path)
  elif ex == '.json':
    df = read_line_json(file_path, encoding=encoding)
  else:
    raise Exception('未知文件格式')
  if columns:
    df = df[columns]
  if info:
    print(f'shape: {df.shape}')
    print(f'columns: {df.columns.tolist()}')
  return df


def read_line_json(filename, encoding='utf-8') -> pd.DataFrame:
  """
  逐行读取json格式的文件
  Args:
    filename: 文件名
    encoding: 文件编码，默认为utf-8
  """
  import json
  records = []
  with open(filename, 'r', encoding=encoding) as file:
    for line in file:
      row = json.loads(line)
      records.append(row)
  return pd.DataFrame(records)


def rdf_by_dir(dir_path, exts=None, ignore_index=True, recursive=False,
               columns=None, info=False) -> pd.DataFrame:
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
  path_list = []
  for p in dir_iter(dir_path, exts=exts, ignore_hidden_files=True,
                    recursive=recursive):
    path_list.append(p)
  dfs = []
  for filename in tqdm(path_list):
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
  for i in gdf_dict.keys():
    level_dict[i] = 0
  for k in range(1, len(gdf_dict.keys())):
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
    if columns_name not in level_dict_new.keys():
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
