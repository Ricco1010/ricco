import csv
import warnings

import geopandas as gpd
import pandas as pd

from ..os import ext


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


def rdxls(filename, sheet_name=0, sheet_contains: str = None, errors='raise'):
  """
  读取excel文件

  :param filename: 文件名
  :param sheet_name: sheet表的名称
  :param sheet_contains: sheet表包含的字符串
  :param errors: 当没有对应sheet时，raise: 抛出错误, coerce: 返回空的dataframe
  :return:
  """
  if sheet_name == 0:
    if sheet_contains is not None:
      df = pd.read_excel(filename, sheet_name=None)
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
        elif errors == 'raise':
          raise ValueError(f'没有包含{sheet_contains}的sheet，请检查')
        else:
          raise KeyError("参数'error'错误, 可选参数为coerce和raise")
  else:
    print(f"sheet:  <'{sheet_name}'>")
  return pd.read_excel(filename, sheet_name=sheet_name)


def rdf(file_path: str,
        sheet_name=0,
        sheet_contains: str = None,
        encoding='utf-8-sig',
        info=False) -> pd.DataFrame:
  """
  常用文件读取函数，支持.csv/.xlsx/.shp
  """
  max_grid()

  if ext(file_path) == '.csv':
    try:
      df = pd.read_csv(file_path, engine='python', encoding=encoding)
    except UnicodeDecodeError:
      df = pd.read_csv(file_path, engine='python')
  elif ext(file_path) in ('.xls', '.xlsx'):
    df = rdxls(file_path, sheet_name=sheet_name, sheet_contains=sheet_contains)
  elif ext(file_path) == '.shp':
    try:
      df = gpd.GeoDataFrame.from_file(file_path)
    except UnicodeEncodeError:
      df = gpd.GeoDataFrame.from_file(file_path, encoding='GBK')
  else:
    raise Exception('未知文件格式')
  if info:
    print(f'shape: {df.shape}')
    print(f'columns: {df.columns}')
  return df


def read_line_json(filename, encoding='utf-8'):
  """
  逐行读取json格式的文件，目前用于金刚石数据读取

  :param filename: 文件名
  :param encoding: 文件编码，默认为utf-8
  :return:
  """
  import json
  records = []
  with open(filename, 'r', encoding=encoding) as file:
    for line in file:
      row = json.loads(line)
      records.append(row)
  return pd.DataFrame(records)


def bigdata2df(filename: str, chunksize: int = 10000,
               code: str = "utf-8") -> pd.DataFrame:
  reader = pd.read_table(filename,
                         encoding=code,
                         sep=",",
                         skip_blank_lines=True,
                         iterator=True)
  loop = True
  chunks = []
  while loop:
    try:
      chunk = reader.get_chunk(chunksize)
      chunk.dropna(axis=0, inplace=True)
      chunks.append(chunk)
    except StopIteration:
      loop = False
      print('Iteration is stopped.')
  df = pd.concat(chunks, ignore_index=True, axis=1)
  return df
