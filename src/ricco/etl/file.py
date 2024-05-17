import csv
import os
import shutil

import fiona
import pandas as pd
from shapely.geometry import shape
from tqdm import tqdm

from ..base import ensure_ext
from ..base import warn_
from ..geometry.util import dumps2x
from ..util.os import dir_iter_list
from ..util.os import ensure_dir
from ..util.os import ensure_dirpath_exist
from ..util.os import extension
from ..util.os import path_name
from ..util.os import remove_path
from ..util.os import single_ext
from ..util.os import split_path
from .extract import rdf
from .extract import rdf_by_dir
from .load import to_file
from .load import to_parts_file


def split2x_by_parts(
    filename: str,
    *,
    parts: int = None,
    to_ext='.csv',
    log=True,
    fn=None,
):
  """
  将文件拆分为多个文件，放置在与文件同名目录下

  Args:
    filename: 文件路径
    parts: 输出的文件个数
    to_ext: 输出文件扩展名
    log: 是否输出文件保存信息
    fn: 处理函数
  """
  # 创建目标目录
  to_ext = ensure_ext(to_ext)
  full_path = os.path.abspath(filename)
  dirpath = path_name(full_path)
  # 读取文件并分批保存
  df = rdf(full_path)
  if fn:
    df = fn(df)
  to_parts_file(df, dirpath, parts=parts, to_ext=to_ext, log=log)


def split2x_by_chunksize(
    filepath: str,
    *,
    chunksize: int = 50000,
    to_ext='.csv',
    log=True,
    fn=None,
    **kwargs,
):
  """
  将文件拆分为多个文件，放置在与文件同名目录下

  Args:
    filepath: 输入的文件路径
    chunksize: 每份文件的数据量
    to_ext: 输出文件扩展名
    log: 是否输出文件保存信息
    fn: 处理函数
  """
  to_ext = ensure_ext(to_ext)
  dirpath = path_name(os.path.abspath(filepath))
  ext = extension(filepath)
  if ext == '.csv':
    for i, _df in enumerate(
        pd.read_csv(filepath, chunksize=chunksize, dtype=str)
    ):
      if fn:
        _df = fn(_df)
      savefile = os.path.join(dirpath, f'part_{str(i).zfill(6)}{to_ext}')
      to_file(_df, savefile, log=log, **kwargs)
  else:
    df = rdf(filepath)
    if fn:
      df = fn(df)
    to_parts_file(df, dirpath,
                  chunksize=chunksize, to_ext=to_ext,
                  log=log)


def split2x(
    filename: str,
    *,
    chunksize: int = None,
    parts: int = None,
    to_ext='.csv',
    log=True,
    fn=None,
):
  """
  将文件拆分为多个文件，放置在与文件同名目录下

  Args:
    filename: 输入的文件路径
    chunksize: 每份文件的数据量
    parts: 输出的文件个数
    to_ext: 输出的文件扩展名
    log: 是否输出文件保存信息
    fn: 处理函数
  """
  assert any([chunksize, parts]), 'chunksize 和 parts必须指定一个'
  to_ext = ensure_ext(to_ext)
  if chunksize:
    split2x_by_chunksize(filename, chunksize=chunksize, to_ext=to_ext, log=log,
                         fn=fn)
  if parts:
    split2x_by_parts(filename, parts=parts, to_ext=to_ext, log=log, fn=fn)


def file_to_x(filepath, to_ext,
              to_dir=None,
              delete=False,
              overwrite=False,
              log=True,
              **kwargs):
  """
  文件格式转换，整体读取并转换，将文件整体加载到内存中再保存为另一种文件格式

  Args:
    filepath: 待转换的文件路径
    to_ext: 要保存的文件扩展名
    to_dir: 要写入的文件路径，默认存放在原目录
    delete: 是否删除原文件，默认不删除
    overwrite: 是否覆盖原文件，默认不覆盖
    log: 是否输出文件保存、删除日志
  """
  to_ext = ensure_ext(to_ext)
  dirpath, filename, ex = split_path(filepath)
  if not to_dir:
    to_dir = dirpath
  to_file_path = os.path.join(to_dir, f'{filename}{to_ext}')
  if not overwrite and os.path.exists(to_file_path):
    warn_(f'文件{filepath}已存在，已跳过', log, 'logging')
    return
  if ex == to_ext:
    ensure_dirpath_exist(to_file_path)
    shutil.copyfile(filepath, to_file_path)
  to_file(rdf(filepath, dtype=str), to_file_path, log=log, **kwargs)
  if delete:
    os.remove(filepath)
    warn_(f'Deleted: {filepath}', log, 'logging')


def dir_file_to_x(from_dir, to_dir,
                  from_ext=None, to_ext=None,
                  recursive=False,
                  delete=False,
                  log=False):
  """转换整个目录中的文件格式"""
  assert from_dir != to_dir, 'from_dir and to_dir must be different'
  assert to_ext is not None, 'to_ext must be specified'
  assert from_ext != to_ext, 'from_ext and to_dir must be different'
  to_ext, from_ext = ensure_ext(to_ext), ensure_ext(from_ext)
  path_list = dir_iter_list(from_dir, exts=from_ext, recursive=recursive)
  print(len(path_list))
  for f in tqdm(path_list):
    file_to_x(f, to_ext, to_dir=to_dir, delete=delete, log=log)


def reshape_files(from_dir, to_dir,
                  from_ext=None, to_ext=None,
                  chunksize: int = 100000,
                  func=None,
                  log=False,
                  **kwargs):
  """
  将文件拆分成小文件，并保存到to_dir中

  Args:
    from_dir: 读取的目录
    to_dir: 保存的目录
    from_ext: 读取的扩展名，默认为None，全部读取
    to_ext: 保存的扩展名，默认为None，若读取文件的扩展名唯一，则使用读文文件的扩展名，反之需要指定
    chunksize: 每个文件的大小
    func: 自定义处理函数
    log: 是否打印日志
  """
  from_dir, to_dir = ensure_dir(from_dir), ensure_dir(to_dir)
  assert from_dir != to_dir, 'from_dir and to_dir must be different'
  assert chunksize >= 1
  n, total_lines, after_lines = 1, 0, 0
  df = pd.DataFrame()
  path_list = dir_iter_list(from_dir, exts=from_ext)
  # 扩展名在不指定输出的情况下，从输入的扩展名中获取
  if not to_ext:
    if ext := single_ext(path_list):
      to_ext = ext
    else:
      raise ValueError('文件中有多个不同扩展名的文件，请指定to_ext')
  for p in tqdm(path_list):
    df_temp = rdf(p)
    total_lines += df_temp.shape[0]
    if func:
      df_temp = func(df_temp)
    after_lines += df_temp.shape[0]
    df = pd.concat([df, df_temp], ignore_index=True)
    while df.shape[0] > chunksize:
      to_file(df[df.index < chunksize],
              os.path.join(to_dir, f'part_{str(n).zfill(6)}{to_ext}'),
              log=log, **kwargs)
      df = df[df.index >= chunksize].reset_index(drop=True)
      n += 1
  to_file(df, os.path.join(to_dir, f'part_{str(n).zfill(6)}{to_ext}'),
          log=log,
          **kwargs)
  print(f'输入文件总数: {len(path_list)}, 输入数据量: {total_lines}')
  print(f'输出文件总数: {n}, 输出数据量: {after_lines}')


def df_iter_by_column(df: pd.DataFrame, by, na='null'):
  """按列的值分组迭代df"""
  for enum, _df in df.groupby(by, as_index=False, dropna=False):
    yield enum if pd.notna(enum) else na, _df


def split_csv_by_column(
    filepath: str, by: str,
    *,
    to_dir: str = None,
    to_ext: str = '.csv',
    merge_file: bool = True,
    chunksize=100000,
):
  """
  将csv文件按指定列的值拆分为多个文件

  Args:
    filepath: csv文件路径
    by: 根据那一列拆分
    to_dir: 要保存的位置，默认与原文件同名目录
    to_ext: 输出的文件扩展名
    merge_file: 是否将每一类数据合并为一个文件，默认合并
    chunksize: 中间文件大小，如内存不足则可适当调低
  """
  dirpath, filename, ex = split_path(filepath)
  to_dir = to_dir or f'{dirpath}/{filename}'
  # 作为中间文件时使用parquet提高速度
  part_ext = '.parquet' if merge_file else to_ext
  print(f'根据"{by}"列将大文件拆分至对应文件夹')
  for i, df in enumerate(pd.read_csv(filepath, chunksize=chunksize, dtype=str)):
    for name, _df in df_iter_by_column(df, by):
      to_file(_df, f'{dirpath}/{filename}/{name}/{i}{part_ext}', log=False)
  if merge_file:
    print('将各个文件夹中的数据合并为一个文件')
    for name in os.listdir(to_dir):
      to_file(
          rdf_by_dir(f'{to_dir}/{name}', exts='.parquet'),
          f'{to_dir}/{name}{to_ext}',
      )
      remove_path(f'{to_dir}/{name}')


def merge_csv_files(dir_path, output_file):
  """
  合并指定目录下的所有CSV文件到一个输出文件中，极低内存消耗

  参数:
  - csv_dir: CSV文件所在的目录
  - output_file: 合并后的输出CSV文件路径
  """
  path_list = dir_iter_list(dir_path, exts='.csv')

  if not path_list:
    print("没有找到csv文件，请检查目录。")

  # 将列表中的第一个csv文件复制并重命名为输出文件
  shutil.copyfile(path_list[0], output_file)

  # 从列表的第二个CSV文件开始逐个处理
  for p in path_list[1:]:
    print(f"正在合并 {p} 到 {output_file} ...")
    with open(p, 'r') as fin:
      # 跳过表头
      next(fin)
      # 以追加模式打开输出文件，并逐行写入内容
      with open(output_file, 'a') as fout:
        for line in fin:
          fout.write(line)
  print(f"所有csv文件已经合并为 '{output_file}'。")


def gdb2csv(
    dir_path,
    output_path=None,
    with_geometry=True,
    geom_format='wkb',
    log=True):
  """gdb文件转换为csv文件"""
  if not output_path:
    output_path = f'{dir_path}.csv'
  if log:
    print(f'Saving: {output_path}')
  with fiona.open(dir_path) as src:
    # 获取图层的字段名称
    columns = list(src.schema['properties'].keys())
    if with_geometry:
      columns.append('geometry')
    with open(output_path, mode='w', newline='', encoding='utf-8') as csv_file:
      writer = csv.DictWriter(csv_file, fieldnames=columns)
      writer.writeheader()
      # 逐行读取GDB文件中的记录
      for line in tqdm(src):
        r = {
          c: line['properties'][c] for c in columns if c != 'geometry'
        }
        if with_geometry:
          r['geometry'] = dumps2x(shape(line['geometry']), geom_format)
        writer.writerow(r)
