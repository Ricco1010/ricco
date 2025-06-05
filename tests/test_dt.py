from ricco.util.dt import auto2date
from datetime import datetime


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
