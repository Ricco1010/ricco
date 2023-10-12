import time
import warnings
from functools import wraps

from shapely.geometry.base import BaseGeometry
from tqdm import tqdm

from .base import is_empty
from .base import second_to_desc


def to_str(func):
  def wrapper(self):
    if self.dst_format:
      return func(self).strftime(self.dst_format)
    else:
      return func(self)

  return wrapper


def progress(func):
  """带有函数名的tqdm进度条"""

  def wrapper(*args, **kwargs):
    tqdm.pandas(desc=func.__name__)
    return func(*args, **kwargs)

  return wrapper


def print_doc(func):
  """打印docstring"""

  def wrapper(*args, **kwargs):
    print(func.__doc__)
    return func(*args, **kwargs)

  return wrapper


def timer(func):
  """函数运行时间统计"""

  def wrapper(*args, **kwargs):
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    duration = end_time - start_time
    desc = second_to_desc(duration)
    print(f'Costs：{duration:.2f} s ({desc})')
    return result

  return wrapper


def check_null(default_rv=None):
  """检查第一个参数是否非空，若为空则直接返回空值"""

  def _check_null(func):
    def wrapper(*args, **kwargs):
      if is_empty(args[0]):
        return default_rv
      return func(*args, **kwargs)

    return wrapper

  return _check_null


def check_str(func):
  """检查第一个参数是否是字符串，若非字符串则警告并返回空值"""

  def wrapper(*args, **kwargs):
    if is_empty(args[0]):
      return
    if not isinstance(args[0], str):
      warnings.warn(f'TypeError:【{args[0]}】')
      return
    return func(*args, **kwargs)

  return wrapper


def check_shapely(func):
  """检查第一个参数是否是shapely格式，若非shapely格式则警告并返回空值"""

  def wrapper(*args, **kwargs):
    if is_empty(args[0]):
      return
    if not isinstance(args[0], BaseGeometry):
      warnings.warn(f'TypeError:【{args[0]}】')
      return
    return func(*args, **kwargs)

  return wrapper


def singleton(fn):
  @wraps(fn)
  def decorator(*args, **kwargs):
    instance = getattr(fn, '__singleinstance', None)
    if instance is None:
      instance = fn(*args, **kwargs)
      setattr(fn, '__singleinstance', instance)
    return instance

  return decorator
