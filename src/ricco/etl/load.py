import csv
import os

import pandas as pd
from shapely.geometry.base import BaseGeometry

from ..geometry.df import auto2shapely
from ..geometry.util import wkb_dumps
from ..util.os import ensure_dirpath_exist
from ..util.os import extension
from ..util.util import first_notnull_value
from . import ALL_EXTS
from .transformer import df_iter


def to_csv_by_line(data: list, filename: str):
  """
  逐行写入csv文件

  Args:
    data: 要写入的数据列表
    filename: 文件名
  """
  with open(filename, 'a') as f:
    csv_write = csv.writer(f, dialect='excel')
    csv_write.writerow(data)


def to_sheets(data: dict, filename: str, index=False):
  """
  将多个dataframe保存到不同的sheet中

  Args:
    data: 要保存的数据集，格式为：{sheet_name: DataFrame}
    filename: 要保存的文件名
    index: 是否保存index
  """
  assert isinstance(data, dict), 'data must be dict'
  with pd.ExcelWriter(filename) as writer:
    for sheet_name, _df in data.items():
      _df.to_excel(writer, sheet_name, index=index)


def to_parquet(df, filepath, index):
  """保存parquet文件，默认将shapely对象转换为wkb格式"""
  shapely_columns = [
    c for c in df if isinstance(first_notnull_value(df[c]), BaseGeometry)
  ]
  for c in shapely_columns:
    df[c] = df[c].apply(wkb_dumps)
  df.to_parquet(filepath, index=index)


def to_file(df: pd.DataFrame, filepath,
            *,
            index=False,
            log=True,
            encoding=None):
  """
  根据文件扩展名，将Dataframe保存为文件

  Args:
    df: 要保存的Dataframe
    filepath: 文件路径，包含扩展名
    index: 是否保存索引，默认不保存
    log: 是否打印保存信息
    encoding: 保存文件的编码
  """
  ensure_dirpath_exist(filepath)
  if log:
    print(f'Saving: {filepath}, Rows：{df.shape[0]}')
  df = df.copy()
  ex = extension(filepath)
  assert ex in ALL_EXTS, f'不支持的文件扩展名：{ex}'

  if ex == '.csv':
    df.to_csv(filepath, index=index, encoding=encoding)
  if ex in ('.pa', '.parquet'):
    to_parquet(df, filepath, index=index)
  if ex in ('.xlsx', '.xls'):
    df.to_excel(filepath, index=index)
  if ex == 'json':
    df.to_json(filepath, orient='records')
  if ex in ('.shp', '.geojson'):
    df = auto2shapely(df)
    df.to_file(filepath, encoding=encoding,
               driver='GeoJSON' if ex == '.geojson' else None)
  if ex in ('.sav', '.zsav'):
    import pyreadstat
    pyreadstat.write_sav(df, filepath)
  if ex == '.feather':
    df.to_feather(filepath, index=index)
  if ex == '.pickle':
    df.to_pickle(filepath)


def to_parts_file(df, dirpath,
                  chunksize=None,
                  parts=None,
                  to_ext='.csv',
                  **kwargs):
  """
  将Dataframe保存为多个文件

  Args:
    df: 要拆分保存的DataFrame
    dirpath: 文件保存的目录
    chunksize: 拆分保存的文件大小
    parts: 拆分保存的文件数量
    to_ext: 文件扩展名
  """
  for i, _df in enumerate(df_iter(df, chunksize=chunksize, parts=parts)):
    savefile = os.path.join(dirpath, f'part_{str(i).zfill(6)}{to_ext}')
    to_file(_df, savefile, **kwargs)
