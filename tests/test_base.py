import numpy as np
import pandas as pd
from shapely.geometry import Point

from ricco.base import is_empty


def test_is_empty():
  assert is_empty(1) is False
  assert is_empty(None) is True
  assert is_empty(np.nan) is True
  assert is_empty([]) is True
  assert is_empty({}) is True
  assert is_empty(pd.DataFrame()) is True
  assert is_empty(Point()) is True
