import re
from datetime import datetime

import pandas as pd


def auto2date(string, errors='raise'):
  if string in ['', None]:
    return None
  string = str(string)

  if '时' in string:
    _hour = re.findall('\d+时', string)[0]
    string = string.split(_hour)[0]

  if ('年' in string) & ('月' in string) & ('日' in string):
    return pd.to_datetime(string, format='%Y年%m月%d日')
  elif ('年' in string) & ('月' in string):
    return pd.to_datetime(string, format='%Y年%m月')
  elif '年' in string:
    return pd.to_datetime(string, format='%Y年')
  else:
    return pd.to_datetime(string, errors=errors)


def is_valid_date(string):
  """判断是否是一个有效的日期字符串"""
  try:
    auto2date(string)
    return True
  except:
    return False


def excel2date(dates, date_type='str'):
  """
  excel的数字样式时间格式转日期格式

  :param dates: 传入excel的日期格式，或ymd的日期格式
  :param date_type: 返回日期类型，str or date
  :return:
  """
  from xlrd import xldate_as_datetime

  if pd.isna(dates):
    return None

  dates = str(dates)
  if re.match('^\d{4,5}$', dates):
    _date = datetime.strftime(xldate_as_datetime(int(dates), 0), '%Y-%m-%d')
  elif is_valid_date(dates):
    _date = datetime.strftime(auto2date(dates), '%Y-%m-%d')
  else:
    _date = None

  if _date:
    if date_type in ('string', 'str', str):
      return _date
    elif date_type in ('date', 'datetime'):
      return datetime.strptime(_date, '%Y-%m-%d')
    else:
      raise ValueError('date_type参数错误，可选参数为str或date')
  else:
    return _date


class DT:
  # TODO(wangyukang): 补充日期方法
  @property
  def today(self):
    return

  @property
  def tomorrow(self):
    return

  @property
  def yesterday(self):
    return

  @property
  def the_day_after_tomorrow(self):
    return

  @property
  def the_day_before_yesterday(self):
    return

  @property
  def one_year_ago(self):
    return

  @property
  def d(self):
    return
