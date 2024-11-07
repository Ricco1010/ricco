import time
import warnings
from functools import wraps

from shapely.geometry.base import BaseGeometry
from tqdm import tqdm

from ..base import is_empty
from ..base import second_to_desc


def progress(func):
  """tqdm进度条（progress_apply）"""

  @wraps(func)
  def wrapper(*args, **kwargs):
    tqdm.pandas(desc=func.__name__)
    __rv = func(*args, **kwargs)
    tqdm.pandas()
    return __rv

  return wrapper


def get_cores():
  import psutil
  return int(
      (psutil.cpu_count(logical=True) + psutil.cpu_count(logical=False)) / 2
  )


def process_multi(func):
  """多线程处理apply任务（parallel_apply）"""

  @run_once
  def init_pandarallel():
    from pandarallel import pandarallel
    pandarallel.initialize(nb_workers=get_cores(), progress_bar=True)

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


def timer(desc=None):
  """函数运行时间统计"""

  def _timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      start_time = time.time()
      result = func(*args, **kwargs)
      end_time = time.time()
      duration = end_time - start_time
      time_desc = second_to_desc(duration)
      title = desc or func.__name__
      print(f'Costs：{duration:.2f} s ({time_desc})，function: {title} ')
      return result

    return wrapper

  return _timer


def check_null(default_rv=None):
  """检查第一个参数是否非空，若为空则直接返回空值"""

  def _check_null(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      if len(args) > 0:
        if is_empty(args[0]):
          return default_rv
      elif len(kwargs) > 0:
        if is_empty(list(kwargs.values())[0]):
          return default_rv
      else:
        raise ValueError('No args or kwargs')
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
      warnings.warn(f'输入值不是shapely格式:【{args[0]}】')
      return
    return func(*args, **kwargs)

  return wrapper


def run_once(func):
  """在一次执行中只运行一次，注：除第一次运行外，后续的不会执行也无返回值"""

  @wraps(func)
  def wrapper(*args, **kwargs):
    if not wrapper.has_run:
      wrapper.has_run = True
      return func(*args, **kwargs)

  wrapper.has_run = False
  return wrapper


def as_staticmethod(cls):
  """将函数添加到类中并作为staticmethod"""

  @wraps(cls)
  def decorator(func):
    setattr(cls, func.__name__, staticmethod(func))
    return func

  return decorator
