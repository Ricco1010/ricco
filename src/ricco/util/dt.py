import datetime as dt
import re
import warnings
from datetime import datetime
from datetime import timedelta
from functools import wraps

import pandas as pd
from dateutil.relativedelta import relativedelta

from .decorator import check_null


def to_str(func):
  """将日期转为字符串的装饰器"""

  @wraps(func)
  def wrapper(self):
    if self.dst_format:
      return func(self).strftime(self.dst_format)
    else:
      return func(self)

  return wrapper


@check_null()
def auto2date(string, errors='raise'):
  """自动检查格式并输出日期"""
  if string in ['', None]:
    return
  string = str(string)

  if '时' in string:
    _hour = re.findall(r'\d+时', string)[0]
    string = string.split(_hour)[0]
  if all([i in string for i in ['年', '月', '日']]):
    return pd.to_datetime(string, format='%Y年%m月%d日')
  if all([i in string for i in ['年', '月']]):
    return pd.to_datetime(string, format='%Y年%m月')
  if '年' in string:
    return pd.to_datetime(string, format='%Y年')
  return pd.to_datetime(string, errors=errors)


def is_valid_date(string, na=False):
  """判断是否是一个有效的日期字符串"""
  if string in ['', None]:
    return na
  try:
    auto2date(string)
    return True
  except Exception:
    return False


@check_null()
def excel2date(dates, date_type='str'):
  """
  excel的数字样式时间格式转日期格式

  Args:
    dates: 传入excel的日期格式，或ymd的日期格式
    date_type: 返回日期类型，str or date
  """
  from xlrd import xldate_as_datetime
  dates = str(dates)
  if re.match('^\d{4,5}$', dates):
    _date = datetime.strftime(xldate_as_datetime(int(dates), 0), '%Y-%m-%d')
  elif is_valid_date(dates):
    _date = datetime.strftime(auto2date(dates), '%Y-%m-%d')
  else:
    return

  if date_type in ('string', 'str', str):
    return _date
  elif date_type in ('date', 'datetime'):
    return datetime.strptime(_date, '%Y-%m-%d')
  else:
    raise ValueError('date_type参数错误，可选参数为str或date')


class DT:
  """
  DT日期类

  Args:
    date: 初始化支持字符串、datetime.date和datetime.datetime格式作为基准日期。不指定时，默认基准日期今天。
    format: 当初始化为字符串时，需要输入format指定日期字符串格式。
    dst_format: 可选。未指定时，类方法输出结果为datetime.date日期格式。指定dst_format时，输出结果为符合dst_format的字符串格式。
  """

  def __init__(self,
               date: (str, dt.date, dt.datetime) = None,
               format='%Y-%m-%d',
               dst_format=None):
    warnings.warn('DT2在版本0.5.38及更新版本中可以使用，详情见util.dt.DT2',
                  DeprecationWarning)
    if date:
      if isinstance(date, str):
        self.date = dt.datetime.strptime(date, format).date()
      elif isinstance(date, dt.datetime):
        self.date = date.date()
      elif isinstance(date, dt.date):
        self.date = date
      else:
        raise TypeError(
            '无法识别的类型，date只能为字符串、datetime.date或datetime.datetime类型')
    else:
      self.date = dt.date.today()
    self.dst_format = dst_format

  @property
  @to_str
  def today(self):
    """今天"""
    return self.date

  @property
  @to_str
  def tomorrow(self):
    """明天"""
    return self.date_move(days=1)

  @property
  @to_str
  def yesterday(self):
    """昨天"""
    return self.date_move(days=-1)

  @property
  @to_str
  def the_day_after_tomorrow(self):
    """后天"""
    return self.date_move(days=2)

  @property
  @to_str
  def the_day_before_yesterday(self):
    """前天"""
    return self.date_move(days=-2)

  @property
  @to_str
  def one_year_ago(self):
    """一年前"""
    return self.date_move(years=-1)

  @property
  @to_str
  def first_day_of_this_month(self):
    """本月第一天"""
    return self.date.replace(day=1)

  @property
  @to_str
  def last_day_of_this_month(self):
    """本月最后一天"""
    return self.date_move(months=1).replace(day=1) + relativedelta(days=-1)

  @property
  @to_str
  def day_half_year_ago(self):
    """半年前"""
    return self.date_move(months=-6)

  def date_move(self, years=0, months=0, days=0):
    """基于当前日期移动日期"""
    return self.date + relativedelta(years=years, months=months, days=days)

  @property
  @to_str
  def monday_of_this_week(self):
    """本周一"""
    weekday = self.date.isoweekday()
    if weekday == 1:
      return self.date
    return self.date - timedelta(weekday - 1)


class DT2:
  def __init__(self,
               date: (str, dt.date, dt.datetime) = None,
               date_format='%Y-%m-%d'):
    """
    DT日期类
    Args:
      date: 初始化支持字符串、datetime.date和datetime.datetime格式作为基准日期。不指定时，默认基准日期今天。
      date_format: 当初始化为字符串时，需要输入format指定日期字符串格式。
    Examples:
      today = '2024-01-31'
      上个月的第一天：
      DT(today).date_move(months=-1).first_day_of_this_month.get()
      --2023-12-01--(class 'datetime.date')
      DT(today).date_move(months=-1).first_day_of_this_month.get(format='%Y %m %d')
      --2023 12 01--(class 'str')
    """
    if date:
      if isinstance(date, str):
        self.date = dt.datetime.strptime(date, date_format).date()
      elif isinstance(date, dt.datetime):
        self.date = date.date()
      elif isinstance(date, dt.date):
        self.date = date
      else:
        raise TypeError(
            '无法识别的类型，date只能为字符串、datetime.date或datetime.datetime类型')
    else:
      self.date = dt.date.today()

  @property
  def today(self):
    """今天"""
    return self

  @property
  def tomorrow(self):
    """明天"""
    return self.date_move(days=1)

  @property
  def yesterday(self):
    """昨天"""
    return self.date_move(days=-1)

  @property
  def the_day_after_tomorrow(self):
    """后天"""
    return self.date_move(days=2)

  @property
  def the_day_before_yesterday(self):
    """前天"""
    return self.date_move(days=-2)

  @property
  def one_year_ago(self):
    """一年前的今天"""
    return self.date_move(years=-1)

  @property
  def first_day_of_this_month(self):
    """本月第一天"""
    self.date = self.date.replace(day=1)
    return self

  @property
  def last_day_of_this_month(self):
    """本月最后一天"""
    self.date = self.date_move(months=1).get().replace(day=1) + relativedelta(days=-1)
    return self

  @property
  def day_half_year_ago(self):
    """半年前的今天"""
    return self.date_move(months=-6)

  @property
  def monday_of_this_week(self):
    """本周的星期一"""
    weekday = self.date.isoweekday()
    if weekday == 1:
      return self
    self.date = self.date - dt.timedelta(weekday - 1)
    return self

  def date_move(self, years=0, months=0, days=0):
    """移动任意年/月/日后的日期，移动数量为正数表示向后移动，负数表示向前移动"""
    self.date = self.date + relativedelta(years=years, months=months, days=days)
    return self

  def get(self, format=None):
    """指定format，输出符合format格式的字符串，否则输出datetime.date类实例"""
    if format:
      return self.date.strftime(format)
    return self.date
