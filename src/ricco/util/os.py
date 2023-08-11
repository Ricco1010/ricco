import datetime
import logging
import os
import zipfile

from .util import ensure_list


def ext(filepath):
  """扩展名"""
  return os.path.splitext(filepath)[1]


def fn(filepath):
  """路径及文件名（不含扩展名）"""
  return os.path.splitext(filepath)[0]


def split_path(filepath, abs=False):
  """将文件路径拆分为文件夹路径、文件名、扩展名三部分"""
  if abs:
    filepath = os.path.abspath(filepath)
  basename = os.path.basename(filepath)
  dir_path = os.path.dirname(filepath)
  return dir_path, fn(basename), ext(basename)


def remove_dir(filepath):
  """
  删除某一目录下的所有文件或文件夹
  :param filepath: 路径
  :return:
  """
  import shutil
  del_list = os.listdir(filepath)
  for f in del_list:
    file_path = os.path.join(filepath, f)
    if os.path.isfile(file_path):
      os.remove(file_path)
    elif os.path.isdir(file_path):
      shutil.rmtree(file_path)
  shutil.rmtree(filepath)


def dir2zip(filepath, delete_exist=False, delete_origin=False):
  """压缩文件夹"""
  zfn = filepath + '.zip'
  if delete_exist:
    if os.path.exists(zfn):
      os.remove(zfn)
      print(f'文件已存在，delete {zfn}')
  print(f'saving {zfn}')
  z = zipfile.ZipFile(zfn, 'w', zipfile.ZIP_DEFLATED)
  for dirpath, dirnames, filenames in os.walk(filepath):
    for filename in filenames:
      filepath_out = os.path.join(dirpath, filename)
      filepath_in = os.path.join(os.path.split(dirpath)[-1], filename)
      z.write(filepath_out, arcname=filepath_in)
  z.close()
  if delete_origin:
    print(f'delete {filepath}')
    remove_dir(filepath)


def get_file_counts(dir_path):
  """获取文件夹中文件的数量"""
  num = 0
  for dirpath, dirnames, filenames in os.walk(dir_path):
    for filename in filenames:
      if filename != '.DS_Store':
        num += 1
  return num


def rm_scratch_file(dir_path, days, rm_hidden_file=False):
  """删除指定天数前修改过的文件"""
  dirs = [
    '/bin', '/sbin', '/usr', '/etc', '/dev', '/Applications', '/Library',
    '/Network', '/System', '/Volumes', '/cores', '/private'
  ]
  for pre in dirs:
    if os.path.abspath(dir_path).startswith(fr'{pre}'):
      raise ValueError('系统目录下的文件不可删除')
  if dir_path == '/':
    raise ValueError('不可指定根目录')
  timeline = datetime.datetime.now() - datetime.timedelta(days)
  # 删除过期文件
  for dirpath, dirnames, filenames in os.walk(dir_path):
    for filename in filenames:
      if not rm_hidden_file:
        continue
      full_path = os.path.join(dirpath, filename)
      m_time = os.path.getmtime(full_path)
      m_time = datetime.datetime.fromtimestamp(m_time)
      if m_time <= timeline:
        os.remove(full_path)
        logging.warning(f'已删除文件：{full_path}')
  # 删除空文件夹
  for dirpath, dirnames, filenames in os.walk(dir_path):
    for dirname in dirnames:
      dir_full_path = os.path.join(dirpath, dirname)
      num = get_file_counts(dir_full_path)
      if num == 0:
        remove_dir(dir_full_path)
        logging.warning(f'已删除空文件夹：{dir_full_path}')


def dir_iter(root, exts: (list, str) = None, abspath=False):
  """
  文件夹中的文件路径生成器，用于遍历文件夹中的文件
  Args:
    root: 文件目录
    exts: 文件扩展名，不指定则返回所有文件
    abspath: 是否返回绝对路径
  """

  for filename in os.listdir(root):
    filepath = os.path.join(root, filename)
    if abspath:
      filepath = os.path.abspath(filepath)
    if exts:
      exts = ensure_list(exts)
      if ext(filepath) in exts:
        yield filepath
    else:
      yield filepath
