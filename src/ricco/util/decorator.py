import time

from tqdm import tqdm


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
    print(f'costs：{end_time - start_time:.2f} s')
    return result

  return wrapper
