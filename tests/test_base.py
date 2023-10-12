import numpy as np
import pandas as pd
from shapely.geometry import Point

from ricco.util.base import is_empty


def test_is_empty():
  assert is_empty(1) == False
  assert is_empty(None) == True
  assert is_empty(np.nan) == True
  assert is_empty([]) == True
  assert is_empty({}) == True
  assert is_empty(pd.DataFrame()) == True
  assert is_empty(Point()) == True
