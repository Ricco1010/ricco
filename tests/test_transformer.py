import pandas as pd
from pandas.testing import assert_frame_equal

from ricco.etl.transformer import round_by_columns
from ricco.etl.transformer import table2dict

df = pd.DataFrame(
    {
      'a': [1, 2],
      'b': ['a', 'b'],
      'c': [1.1111, 2.2222],
      'd': [0.12344, 0.45678]
    }
)


def test_table2dict():
  assert table2dict(df) == {1: 'a', 2: 'b'}
  assert table2dict(df, 'b', 'c') == {'a': 1.1111, 'b': 2.2222}


def test_round_by_columns():
  assert_frame_equal(
      round_by_columns(df, ['c', 'd']),
      pd.DataFrame(
          {
            'a': [1, 2],
            'b': ['a', 'b'],
            'c': [1.11, 2.22],
            'd': [0.1234, 0.4568]
          }
      )
  )
