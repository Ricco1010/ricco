import logging
import os
import shutil
import warnings
import zipfile
from datetime import datetime
from datetime import timedelta
from pathlib import Path

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
      logging.warning(f'Deleted:"{path}"')
  else:
    warnings.warn(f'Path not found:"{path}"')


def ensure_dirpath_exist(filepath):
  """确保目录存在，不存在则创建"""
  dir_path = os.path.dirname(filepath)
  if not os.path.exists(dir_path):
    os.makedirs(dir_path)
    logging.warning(f'Created: "{dir_path}"')


def file2zip(filepath, overwrite=False, delete_origin=False):
  """将一个文件压缩为zip格式"""
  zfn = path_name(filepath) + '.zip'
  if os.path.exists(zfn) and not overwrite:
    raise FileExistsError(f'"{zfn}"已存在')
  logging.warning(f'Compressing: "{filepath}"')
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
    raise FileExistsError(f'"{zfn}"已存在')
  z = zipfile.ZipFile(zfn, 'w', zipfile.ZIP_DEFLATED)
  for dirpath, _, filenames in os.walk(dir_path):
    for filename in filenames:
      f_o = str(os.path.join(dirpath, filename))
      f_i = str(os.path.join(os.path.split(dirpath)[-1], filename))
      z.write(f_o, f_i)
  z.close()
  if delete_origin:
    remove_path(dir_path)


def count_files(dir_path):
  """统计文件夹中文件的数量"""
  num = 0
  for dirpath, dirnames, filenames in os.walk(dir_path):
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
      logging.warning(f'Deleted:"{file}"')
  # 删除空文件夹
  for dirpath, dirnames, _ in os.walk(dir_path):
    for dirname in dirnames:
      dir_full_path = os.path.join(dirpath, dirname)
      num = count_files(dir_full_path)
      if num == 0:
        remove_path(dir_full_path)


def remove_ds_store(dir_path):
  """删除文件夹中的.DS_Store文件"""
  protect_dir(dir_path)
  for i in dir_iter(dir_path, recursive=True, ignore_hidden_files=False):
    if i.endswith('.DS_Store'):
      remove_path(i)


def dir_iter(root,
             exts: (list, str) = None,
             abspath=False,
             recursive=False,
             ignore_hidden_files=True):
  """
  文件夹中的文件路径生成器，用于遍历文件夹中的文件

  Args:
    root: 文件目录
    exts: 文件扩展名，不指定则返回所有文件
    abspath: 是否返回绝对路径
    recursive: 是否循环遍历更深层级的文件，默认只返回当前目录下的文件
    ignore_hidden_files: 是否忽略隐藏文件
  """
  if exts:
    exts = ensure_list(exts)

  for dirpath, _, filenames in os.walk(root):
    for _name in filenames:
      if ignore_hidden_files and _name.startswith('.'):
        continue
      filepath = os.path.join(dirpath, _name)
      filepath = os.path.abspath(filepath) if abspath else filepath
      # 不符合扩展名要求忽略
      if exts and extension(_name) not in exts:
        continue
      # 仅需要当前目录时，dirpath和root不相同的过滤掉
      if not recursive and dirpath != root:
        continue
      yield filepath


def dir_iter_list(root,
                  exts: (list, str) = None,
                  abspath=False,
                  recursive=False,
                  reverse=False):
  """
  文件夹中的文件路径列表

  Args:
    root: 文件目录
    exts: 文件扩展名，不指定则返回所有文件
    abspath: 是否返回绝对路径
    recursive: 是否循环遍历更深层级的文件，默认只返回当前目录下的文件
    reverse: 路径列表是否倒序
  """
  path_list = []
  for p in dir_iter(root, exts, abspath, recursive, ignore_hidden_files=True):
    path_list.append(p)
  return sorted(path_list, reverse=reverse)


def single_ext(path_list):
  """获取文件列表中所有文件的扩展名，如果只有一个则返回该扩展名"""
  ext_list = list(set([extension(p) for p in path_list]))
  if len(ext_list) == 1:
    return ext_list[0]


class OssPath:
  def __init__(self, path, bucket=None):
    """
    OSS路径类，确保不同类型的地址属性统一

    Args:
      path: 路径，完整路径或bucket后的部分路径
      bucket: 默认从完整路径中获取，当为部分路径时需指定Bucket
    """

    if path.startswith('oss://'):
      pass
    elif bucket:
      path = os.path.join('oss:///', bucket, path)
    else:
      raise Exception('Bucket name is required')

    self.parts = Path(path).parts

    if bucket:
      assert bucket == self.parts[1], 'Bucket name does not match'

  @property
  def bucket(self):
    """Bucket"""
    return self.parts[1]

  @property
  def driver(self):
    """Driver"""
    return self.parts[0]

  @property
  def path_short(self):
    """短路径"""
    if len(self.parts) > 2:
      return str(os.path.join(*self.parts[2:]))
    return ''

  @property
  def path_full(self):
    """完整路径"""
    return str(os.path.join(f'oss:///{self.bucket}', self.path_short))
