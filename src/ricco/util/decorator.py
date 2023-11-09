import time
import warnings
from functools import wraps

from shapely.geometry.base import BaseGeometry
from tqdm import tqdm

from .base import is_empty
from .base import second_to_desc


def to_str(func):
  @wraps(func)
  def wrapper(self):
    if self.dst_format:
      return func(self).strftime(self.dst_format)
    else:
      return func(self)

  return wrapper


def progress(func):
  """tqdm进度条（progress_apply）"""

  @wraps(func)
  def wrapper(*args, **kwargs):
    tqdm.pandas(desc=func.__name__)
    return func(*args, **kwargs)

  return wrapper


def process_multi(func):
  """多线程处理apply任务（parallel_apply）"""

  @run_once
  def init_pandarallel():
    from pandarallel import pandarallel
    pandarallel.initialize(progress_bar=True)

  @wraps(func)
  def wrapper(*args, **kwargs):
    init_pandarallel()
    return func(*args, **kwargs)

  return wrapper


def print_doc(func):
  """打印docstring"""

  @wraps(func)
  def wrapper(*args, **kwargs):
    print(func.__doc__)
    return func(*args, **kwargs)

  return wrapper


def timer(func):
  """函数运行时间统计"""

  @wraps(func)
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
    @wraps(func)
    def wrapper(*args, **kwargs):
      if is_empty(args[0]):
        return default_rv
      return func(*args, **kwargs)

    return wrapper

  return _check_null


def check_str(func):
  """检查第一个参数是否是字符串，若非字符串则警告并返回空值"""

  @wraps(func)
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

  @wraps(func)
  def wrapper(*args, **kwargs):
    if is_empty(args[0]):
      return
    if not isinstance(args[0], BaseGeometry):
      warnings.warn(f'TypeError:【{args[0]}】')
      return
    return func(*args, **kwargs)

  return wrapper


def singleton(func):
  """运行一次后将结果保存，下次直接获取"""

  @wraps(func)
  def decorator(*args, **kwargs):
    instance = getattr(func, '__single_instance', None)
    if instance is None:
      instance = func(*args, **kwargs)
      setattr(func, '__single_instance', instance)
    return instance

  return decorator


def run_once(func):
  """在一次执行中只运行一次，注：除第一次运行外，后续的不会执行也无返回值"""

  @wraps(func)
  def wrapper(*args, **kwargs):
    if not wrapper.has_run:
      wrapper.has_run = True
      return func(*args, **kwargs)

  wrapper.has_run = False
  return wrapper
