import csv
import os

import pandas as pd

from ..geometry.df import auto2shapely
from ..util.os import ensure_dirpath_exist
from ..util.os import extension
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


def to_sheets(data: dict, filename: str):
  """
  将多个dataframe保存到不同的sheet中
  Args:
      data: 要保存的数据集，格式为：{sheet_name: DataFrame}
      filename: 要保存的文件名
  """
  assert isinstance(data, dict), 'data must be dict'
  with pd.ExcelWriter(filename) as writer:
    for sheet_name, data in data.items():
      data.to_excel(writer, sheet_name)


def to_file(df: pd.DataFrame, filepath, index=False, log=True):
  """将df保存为文件"""
  ensure_dirpath_exist(filepath)
  if log:
    print(f'Saving: {filepath}, Rows：{df.shape[0]}')
  df = df.copy()
  exts = extension(filepath)
  if exts == '.csv':
    df.to_csv(filepath, index=index)
  elif exts == '.parquet':
    df.to_parquet(filepath, index=index)
  elif exts in ('.xlsx', '.xls'):
    df.to_excel(filepath, index=index)
  elif exts == '.shp':
    df = auto2shapely(df)
    df.to_file(filepath)
  else:
    raise ValueError(f'不支持的文件扩展名：{exts}')


def to_parts_file(df, dirpath,
                  chunksize=None,
                  parts=None,
                  to_ext='.csv',
                  log=True):
  """
  将df保存为多个文件
  Args:
    df: 要拆分保存的DataFrame
    dirpath: 文件保存的目录
    chunksize: 拆分保存的文件大小
    parts: 拆分保存的文件数量
    to_ext: 文件扩展名
    log: 是否打印日志
  """
  for i, _df in enumerate(df_iter(df, chunksize=chunksize, parts=parts)):
    savefile = os.path.join(dirpath, f'part_{str(i).zfill(6)}{to_ext}')
    to_file(_df, savefile, log=log)
