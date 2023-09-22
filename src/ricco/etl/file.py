import os
import shutil
import warnings

import pandas as pd
from tqdm import tqdm

from ..util.os import dir_iter_list
from ..util.os import ensure_dir
from ..util.os import ensure_dirpath_exist
from ..util.os import extension
from ..util.os import path_name
from ..util.os import single_ext
from ..util.os import split_path
from .extract import rdf
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
  dirpath = path_name(os.path.abspath(filepath))
  ext = extension(filepath)
  if ext == '.csv':
    for i, _df in enumerate(
        pd.read_csv(filepath, chunksize=chunksize, dtype=str)
    ):
      if fn:
        _df = fn(_df)
      savefile = os.path.join(dirpath, f'part_{str(i).zfill(6)}{to_ext}')
      to_file(_df, savefile, log=log)
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
  if chunksize:
    split2x_by_chunksize(filename, chunksize=chunksize, to_ext=to_ext, log=log,
                         fn=fn)
  if parts:
    split2x_by_parts(filename, parts=parts, to_ext=to_ext, log=log, fn=fn)


def file_to_x(filepath, to_ext,
              to_dir=None,
              delete=False,
              overwrite=False,
              log=True):
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
  dirpath, filename, ex = split_path(filepath)
  if not to_dir:
    to_dir = dirpath
  to_file_path = os.path.join(to_dir, f'{filename}{to_ext}')
  if not overwrite and os.path.exists(to_file_path):
    if log:
      warnings.warn(f'文件{filepath}已存在，已跳过')
    return
  if ex == to_ext:
    ensure_dirpath_exist(to_file_path)
    shutil.copyfile(filepath, to_file_path)
  to_file(rdf(filepath, dtype=str), to_file_path, log=log)
  if delete:
    os.remove(filepath)
    if log:
      print(f'Deleted: {filepath}')


def dir_file_to_x(from_dir, to_dir,
                  from_ext=None, to_ext=None,
                  recursive=False,
                  delete=False,
                  log=False):
  """转换整个目录中的文件格式"""
  assert from_dir != to_dir, 'from_dir and to_dir must be different'
  assert to_ext is not None, 'to_ext must be specified'
  assert from_ext != to_ext, 'from_ext and to_dir must be different'

  path_list = dir_iter_list(from_dir, exts=from_ext, recursive=recursive)
  print(len(path_list))
  for f in tqdm(path_list):
    file_to_x(f, to_ext, to_dir=to_dir, delete=delete, log=log)


def reshape_files(from_dir, to_dir,
                  from_ext=None, to_ext=None,
                  chunksize: int = 100000,
                  func=None,
                  log=False):
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
              log=log)
      df = df[df.index >= chunksize].reset_index(drop=True)
      n += 1
  to_file(df, os.path.join(to_dir, f'part_{str(n).zfill(6)}{to_ext}'), log=log)
  print(f'输入文件总数: {len(path_list)}, 输入数据量: {total_lines}')
  print(f'输出文件总数: {n}, 输出数据量: {after_lines}')
