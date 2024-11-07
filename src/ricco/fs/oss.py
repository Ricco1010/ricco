import os.path

from ..base import ensure_list
from ..util.os import extension
from ..util.os import split_path
from .util import bucket_from_path
from .util import ensure_dir
from .util import ensure_osspath_valid
from .util import progress_bar


def oss_client(
    *,
    bucket_name,
    access_key,
    secret_key,
    endpoint=None,
    region=None
):
  """
  创建oss client

  Args:
    bucket_name: bucket名称
    access_key: access_key
    secret_key: secret_key
    endpoint: oss endpoint，默认为“https://oss-cn-hangzhou.aliyuncs.com”
    region: oss region，默认为“cn-hangzhou”
  """
  import oss2
  return oss2.Bucket(
      auth=oss2.Auth(access_key, secret_key),
      endpoint=endpoint or 'https://oss-cn-hangzhou.aliyuncs.com',
      bucket_name=bucket_name,
      region=region or 'cn-hangzhou'
  )


class OssUtils:
  def __init__(self, *, work_path, access_key, secret_key,
               endpoint=None, region=None):
    """
    oss工具类，所有操作均可使用完整路径或work_path的相对路径

    Args:
      work_path: 工作目录，以“oss:///”开头
      access_key: 有work_path权限的access_key
      secret_key: 有work_path权限的secret_key
      endpoint: oss endpoint，默认为“https://oss-cn-hangzhou.aliyuncs.com”
      region: oss region，默认为“cn-hangzhou”
    """
    import oss2
    self.oss2 = oss2
    self.work_path = ensure_dir(ensure_osspath_valid(work_path))
    self.bucket_name = bucket_from_path(work_path)
    self.client = oss_client(
        bucket_name=self.bucket_name,
        access_key=access_key,
        secret_key=secret_key,
        endpoint=endpoint,
        region=region
    )

  @property
  def _prefix(self):
    """oss前缀 + bucket"""
    return f'oss:///{self.bucket_name}/'

  def abspath(self, _path):
    if _path.startswith('oss://'):
      _path = ensure_osspath_valid(_path)
      assert _path.startswith(
          self.work_path), f'必须为“{self.work_path}”的子目录'
      return _path
    return f'{self.work_path}{_path}'

  def object_path(self, _path):
    """将文件路径转为oss2的输入路径，即Bucket之后的路径"""
    _path = self.abspath(_path)
    if _path.endswith('/'):
      return os.path.relpath(_path, self._prefix) + '/'
    return os.path.relpath(_path, self._prefix)

  def upload(self, path_local, path_remote=None, *, overwrite=False):
    """
    上传文件到oss中

    Args:
      path_local: 本地文件路径
      path_remote: oss路径及文件名，若不指定则上传为work_path下的同名文件
    """
    if not path_remote:
      path_remote = ''.join(split_path(path_local)[-2:])
    path_remote = self.object_path(path_remote)
    if not overwrite and self.exist(self._prefix + path_remote):
      raise FileExistsError(f'文件已存在：{path_remote}')
    self.client.put_object_from_file(
        path_remote,
        path_local,
        progress_callback=progress_bar,
    )

  def download(self, path_remote, path_local=None, *, overwrite=False):
    """
    从oss中下载文件

    Args:
      path_remote: oss路径及文件名
      path_local: 本地文件路径，若不指定则下载为work_path下的同名文件
    """
    if not path_local:
      path_local = ''.join(split_path(path_remote)[-2:])
    if not overwrite and os.path.exists(path_local):
      raise FileExistsError(f'文件已存在：{path_remote}')
    path_remote = self.object_path(path_remote)
    self.client.get_object_to_file(
        path_remote, path_local,
        progress_callback=progress_bar,
    )

  def mkdir(self, dir_path):
    """创建目录"""
    dir_path = ensure_dir(dir_path)
    dir_path = self.object_path(dir_path)
    self.client.put_object(dir_path, '')

  def rm(self, _path):
    """删除文件或目录"""
    self.client.delete_object(self.object_path(_path))

  def exist(self, _path):
    """判断文件是否存在"""
    return self.client.object_exists(self.object_path(_path))

  def dir_iter(self, dir_path=None, exts=None, recursive=False):
    """
    遍历目录下的文件

    Args:
      dir_path: 目录路径，如不指定则遍历实例化时指定的work_path
      exts: 文件后缀
      recursive: 是否递归遍历
    """
    exts = ensure_list(exts)
    dir_path = ensure_dir(dir_path)
    dir_path = self.object_path(dir_path)
    for obj in self.oss2.ObjectIterator(
        self.client, prefix=dir_path,
        delimiter='' if recursive else '/'
    ):
      if obj.is_prefix():
        continue
      if exts and extension(obj.key) not in exts:
        continue
      if obj.key.endswith('/'):
        continue
      yield self._prefix + obj.key
