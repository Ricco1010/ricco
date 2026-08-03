import pandas as pd

from ricco.util.random import ramdom_lnglat
from ricco.util.random import random_by_prob
from ricco.util.random import random_date
from ricco.util.random import random_name
from ricco.util.random import random_room_number


def test_random_name():
  name = random_name()
  assert isinstance(name, str)
  assert 2 <= len(name) <= 3


def test_random_date():
  import datetime
  import random
  now = datetime.datetime.now()
  tsp = int(datetime.datetime.timestamp(now))
  tsp = random.randrange(0, tsp)
  d = datetime.datetime.fromtimestamp(tsp).strftime("%Y%m%d")
  assert isinstance(d, str)
  assert len(d) == 8


def test_random_room_number():
  room = random_room_number()
  assert isinstance(room, str)
  assert 2 <= len(room) <= 4

  room_unit = random_room_number(unit=True)
  assert '单元' in room_unit


def test_random_by_prob():
  result = random_by_prob({'a': 0.5, 'b': 0.5})
  assert result in ('a', 'b')


def test_ramdom_lnglat():
  df = pd.DataFrame({'x': [1, 2, 3]})
  result = ramdom_lnglat(df)
  assert 'lng' in result.columns
  assert 'lat' in result.columns
  assert len(result) == 3
  assert result['lng'].between(72, 138).all()
  assert result['lat'].between(0, 56).all()
