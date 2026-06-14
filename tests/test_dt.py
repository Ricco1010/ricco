from datetime import datetime

from ricco.util.dt import auto2date
from ricco.util.dt import excel2date
from ricco.util.dt import is_valid_date


def test_auto2date():
  assert auto2date('2020-01-01') == datetime(2020, 1, 1)
  assert auto2date('2020-01') == datetime(2020, 1, 1)
  assert auto2date('2020/01/01') == datetime(2020, 1, 1)
  assert auto2date('2020/01') == datetime(2020, 1, 1)
  assert auto2date('2020年1月1日') == datetime(2020, 1, 1)
  assert auto2date('2020年1月') == datetime(2020, 1, 1)
  assert auto2date('2020.1.1') == datetime(2020, 1, 1)
  assert auto2date('2020.1') == datetime(2020, 1, 1)
  assert auto2date(None) is None
  assert auto2date(123) is None
  assert auto2date('') is None


def test_is_valid_date():
  assert is_valid_date('2020-01-01') is True
  assert is_valid_date('2020/01/01') is True
  assert is_valid_date('20200101') is True
  assert is_valid_date('not a date') is False
  assert is_valid_date('') is False
  assert is_valid_date(None) is False


def test_excel2date():
  result = excel2date('2020-01-01')
  assert isinstance(result, str)
  assert '2020' in result

  from datetime import date
  result_date = excel2date('2020-01-01', date_type='date')
  assert isinstance(result_date, (date, datetime))
