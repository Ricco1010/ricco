import logging
import os
import shutil
import time
import warnings
import zipfile
from datetime import datetime
from datetime import timedelta

from ..base import ensure_list


def protect_dir(path):
  """检查路径是否为系统目录"""
  if os.path.isdir(path):
    if path == '/':
      raise ValueError('不可指定根目录')
    dirs = [
      '/bin', '/sbin', '/usr', '/etc', '/dev', '/Applications', '/Library',
      '/Network', '/System', '/Volumes', '/cores', '/private'
    ]
    for pre in dirs:
      if os.path.abspath(path).startswith(fr'{pre}'):
        raise ValueError('系统目录下的文件不可删除')


def ext(filepath):
  """获取文件扩展名"""
  return extension(filepath)


def extension(filepath):
  """获取文件扩展名"""
  return os.path.splitext(filepath)[1]


def fn(filepath):
  """路径及文件名（不含扩展名）"""
  return path_name(filepath)


def path_name(filepath):
  """路径及文件名（不含扩展名）"""
  return os.path.splitext(filepath)[0]


def split_path(filepath, abspath=False):
  """将文件路径拆分为文件夹路径、文件名、扩展名三部分"""
  if abspath:
    filepath = os.path.abspath(filepath)
  basename = os.path.basename(filepath)
  return os.path.dirname(filepath), path_name(basename), extension(basename)


def ensure_dir(dirpath: str):
  """确保路径为文件夹格式（以斜杠“/”结尾）"""
  if not dirpath.endswith('/'):
    return dirpath + '/'
  return dirpath


def remove_path(path, log=True):
  """删除文件或文件夹"""
  if os.path.exists(path):
    os.remove(path) if os.path.isfile(path) else shutil.rmtree(path)
    if log:
      logging.warning(f'Deleted:{path}')
  else:
    warnings.warn(f'NotFound:{path}')


def ensure_dirpath_exist(filepath):
  """确保目录存在，不存在则创建"""
  dir_path = os.path.dirname(filepath)
  if not os.path.exists(dir_path):
    os.makedirs(dir_path)
    logging.warning(f'Created:{dir_path}')


def file2zip(filepath, overwrite=False, delete_origin=False):
  """将一个文件压缩为zip格式"""
  zfn = path_name(filepath) + '.zip'
  if os.path.exists(zfn) and not overwrite:
    raise FileExistsError(f'{zfn}')
  logging.warning(f'Compressing:{filepath}')
  with zipfile.ZipFile(zfn, 'w', zipfile.ZIP_DEFLATED) as zipf:
    zipf.write(filepath, arcname=os.path.basename(filepath))
  if delete_origin:
    remove_path(filepath)


def dir2zip(dir_path, overwrite=False, delete_origin=False):
  """
  压缩文件夹

  Args:
    dir_path: 文件夹路径
    overwrite: 是否覆盖已有文件
    delete_origin: 是否删除原文件
  """
  protect_dir(dir_path)
  zfn = f'{dir_path}.zip'
  if os.path.exists(zfn) and not overwrite:
    raise FileExistsError(f'{zfn}')
  z = zipfile.ZipFile(zfn, 'w', zipfile.ZIP_DEFLATED)
  for _root, _, filenames in os.walk(dir_path):
    for filename in filenames:
      f_o = str(os.path.join(_root, filename))
      f_i = str(os.path.join(os.path.split(_root)[-1], filename))
      z.write(f_o, f_i)
  z.close()
  if delete_origin:
    remove_path(dir_path)


def count_files(dir_path):
  """统计文件夹中文件的数量"""
  num = 0
  for _, __, filenames in os.walk(dir_path):
    for filename in filenames:
      if filename != '.DS_Store':
        num += 1
  return num


def rm_scratch_file(dir_path, days, recursive=False, rm_hidden_file=False,
                    exts=None):
  """删除指定天数前修改过的文件"""
  protect_dir(dir_path)
  timeline = datetime.now() - timedelta(days)
  # 删除过期文件
  for file in dir_iter(dir_path, abspath=True, recursive=recursive,
                       ignore_hidden_files=not rm_hidden_file, exts=exts):
    m_time = os.path.getmtime(file)
    m_time = datetime.fromtimestamp(m_time)
    if m_time <= timeline:
      os.remove(file)
      logging.warning(f'Deleted:{file}')
  # 删除空文件夹
  for _root, dirs, _ in os.walk(dir_path):
    for dir_name in dirs:
      dir_full_path = os.path.join(_root, dir_name)
      num = count_files(dir_full_path)
      if num == 0:
        remove_path(dir_full_path)


def remove_ds_store(dir_path):
  """删除文件夹中的.DS_Store文件"""
  protect_dir(dir_path)
  for i in dir_iter(dir_path, recursive=True, ignore_hidden_files=False):
    if i.endswith('.DS_Store'):
      remove_path(i)


def dir_iter(dir_path,
             exts: (list, str) = None,
             abspath=False,
             recursive=False,
             ignore_hidden_files=True):
  """
  文件夹中的文件路径生成器，用于遍历文件夹中的文件

  Args:
    dir_path: 文件目录
    exts: 文件扩展名，不指定则返回所有文件
    abspath: 是否返回绝对路径
    recursive: 是否循环遍历更深层级的文件，默认只返回当前目录下的文件
    ignore_hidden_files: 是否忽略隐藏文件
  """
  if exts:
    exts = ensure_list(exts)

  for _root, _, filenames in os.walk(dir_path):
    for _name in filenames:
      if ignore_hidden_files and _name.startswith('.'):
        continue
      filepath = os.path.join(_root, str(_name))
      filepath = os.path.abspath(filepath) if abspath else filepath
      # 不符合扩展名要求忽略
      if exts and extension(_name) not in exts:
        continue
      # 仅需要当前目录时，dirpath和root不相同的过滤掉
      if not recursive and _root != dir_path:
        continue
      yield filepath


def dir_iter_list(dir_path,
                  exts: (list, str) = None,
                  abspath=False,
                  recursive=False,
                  reverse=False):
  """
  文件夹中的文件路径列表

  Args:
    dir_path: 文件目录
    exts: 文件扩展名，不指定则返回所有文件
    abspath: 是否返回绝对路径
    recursive: 是否循环遍历更深层级的文件，默认只返回当前目录下的文件
    reverse: 路径列表是否倒序
  """
  path_list = [
    p for p in
    dir_iter(dir_path, exts, abspath, recursive, ignore_hidden_files=True)
  ]
  return sorted(path_list, reverse=reverse)


def single_ext(path_list):
  """获取文件列表中所有文件的扩展名，如果只有一个则返回该扩展名"""
  ext_list = list(set([extension(p) for p in path_list]))
  if len(ext_list) == 1:
    return ext_list[0]


def getsize(filepath):
  """获取文件大小"""
  from psutil._common import bytes2human
  return bytes2human(os.path.getsize(filepath))


def move_file_with_metadata(src, dst):
  """移动文件并保留元数据"""
  # 确保源文件存在
  if not os.path.isfile(src):
    print(f'FileNotExist: {src}')
    return
  if os.path.isfile(dst):
    print(f'FileExist：{dst}')
    os.remove(dst)
  # 复制源文件到目标位置
  shutil.copy2(src, dst)
  # 获取源文件的元数据
  stat = os.stat(src)
  # 修改目标文件的访问和修改时间
  os.utime(dst, (stat.st_atime, stat.st_mtime))
  # 删除源文件
  os.remove(src)
  print(f'Move:{src}-->{dst}')


def is_using_in(filepath, hours):
  """判断文件是否在某个时间段内修改过"""
  # 获取当前时间戳
  current_time = time.time()
  # 获取文件的最后修改时间戳
  file_mod_time = os.path.getmtime(filepath)
  # 计算时间差（秒）
  _diff = current_time - file_mod_time
  # 检查文件是否在指定的小时内被修改
  return _diff <= hours * 3600
