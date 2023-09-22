import datetime as dt
import re
from datetime import datetime

import pandas as pd
from dateutil.relativedelta import relativedelta
from .decorator import check_null
from .decorator import to_str


@check_null
def auto2date(string, errors='raise'):
  """自动检查格式并输出日期"""
  if string in ['', None]:
    return
  string = str(string)

  if '时' in string:
    _hour = re.findall('\d+时', string)[0]
    string = string.split(_hour)[0]
  if ('年' in string) & ('月' in string) & ('日' in string):
    return pd.to_datetime(string, format='%Y年%m月%d日')
  if ('年' in string) & ('月' in string):
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


def excel2date(dates, date_type='str'):
  """
  excel的数字样式时间格式转日期格式
  Args:
    dates: 传入excel的日期格式，或ymd的日期格式
    date_type: 返回日期类型，str or date
  """
  from xlrd import xldate_as_datetime

  if pd.isna(dates):
    return

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

  def __init__(self,
               date: (str, dt.date, dt.datetime) = None,
               format='%Y-%m-%d',
               dst_format=None):
    """
    DT日期类
    Args:
      date: 初始化支持字符串、datetime.date和datetime.datetime格式作为基准日期。不指定时，默认基准日期今天。
      format: 当初始化为字符串时，需要输入format指定日期字符串格式。
      dst_format: 可选。未指定时，类方法输出结果为datetime.date日期格式。指定dst_format时，输出结果为符合dst_format的字符串格式。
    """
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
    return self.date

  @property
  @to_str
  def tomorrow(self):
    return self.date_move(days=1)

  @property
  @to_str
  def yesterday(self):
    return self.date_move(days=-1)

  @property
  @to_str
  def the_day_after_tomorrow(self):
    return self.date_move(days=2)

  @property
  @to_str
  def the_day_before_yesterday(self):
    return self.date_move(days=-2)

  @property
  @to_str
  def one_year_ago(self):
    return self.date_move(years=-1)

  @property
  @to_str
  def first_day_of_this_month(self):
    return self.date.replace(day=1)

  @property
  @to_str
  def last_day_of_this_month(self):
    return self.date_move(months=1).replace(day=1) + relativedelta(days=-1)

  @property
  @to_str
  def day_half_year_ago(self):
    return self.date_move(months=-6)

  def date_move(self, years=0, months=0, days=0):
    return self.date + relativedelta(years=years, months=months, days=days)
