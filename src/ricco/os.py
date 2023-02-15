import os
import zipfile


def ext(filepath):
  """扩展名"""
  return os.path.splitext(filepath)[1]


def fn(filepath):
  """路径及文件名（不含扩展名）"""
  return os.path.splitext(filepath)[0]


def mkdir_2(path: str):
  """新建文件夹，忽略存在的文件夹"""
  if not os.path.isdir(path):
    os.makedirs(path)


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


def dir2zip(filepath, delete_exist=True, delete_origin=False):
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
