import os.path
import stat

from ..base import ensure_list
from ..util.os import ensure_dirpath_exist
from ..util.os import extension


def get_sftp_client(
    *,
    hostname,
    port,
    username,
    password
):
  import paramiko
  ssh = paramiko.SSHClient()
  ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  ssh.connect(hostname=hostname,
              port=port,
              username=username,
              password=password)
  return ssh.open_sftp()


class SFTP:
  def __init__(self, *, hostname, port, username, password):
    self._sftp = get_sftp_client(
        hostname=hostname,
        port=port,
        username=username,
        password=password
    )

  @property
  def workdir(self):
    return self._sftp.getcwd() or '/'

  def isfile(self, path):
    """判断是否为文件"""
    return stat.S_ISREG(self._sftp.stat(path).st_mode)

  def isdir(self, path):
    """判断是否为目录"""
    return stat.S_ISDIR(self._sftp.stat(path).st_mode)

  def chdir(self, path):
    """切换工作目录"""
    self._sftp.chdir(path)
    print(self.listdir())

  def listdir(self, path=None, recursive=False):
    """列出目录下的所有文件和子目录，返回列表"""
    path = path or self.workdir
    if not recursive:
      return self._sftp.listdir(path)
    else:
      dirs = []
      for item in self._sftp.listdir(path):
        item_path = os.path.join(path, item)
        if self.isdir(item_path):
          dirs.append(item_path)
          dirs.extend(self.listdir(item_path, recursive=True))
        else:
          dirs.append(item_path)
      return sorted(dirs)

  def dir_iter(self, path=None, recursive=False, exts=None):
    """遍历目录，返回所有文件路径 """
    for item in self.listdir(path, recursive):
      if self.isfile(item):
        if exts:
          exts = ensure_list(exts)
          if extension(item) in exts:
            yield item
        else:
          yield item

  def download(self, remote_path, local_dir):
    """下载单个文件或整个目录"""
    assert os.path.isdir(local_dir), '本地路径必须是一个目录'
    os.makedirs(local_dir, exist_ok=True)
    if self.isfile(remote_path):
      filename = os.path.basename(remote_path)
      local_path = os.path.join(local_dir, filename)
      ensure_dirpath_exist(local_path)
      self._sftp.get(remote_path, local_path)
    elif self.isdir(remote_path):
      files = [
        i for i in self.listdir(remote_path, recursive=True) if self.isfile(i)
      ]
      print(f'共{len(files)}个文件')
      for i, file in enumerate(files):
        print(f'正在下载第{i + 1}个文件，{file}')
        objname = os.path.basename(remote_path.rstrip('/'))
        subpath = os.path.relpath(file, remote_path)
        local_path = os.path.join(local_dir, objname, subpath)
        ensure_dirpath_exist(local_path)
        self._sftp.get(file, local_path)
    else:
      raise Exception(f'未知的路径类型：{remote_path}')
