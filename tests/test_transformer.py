import pandas as pd
from pandas.testing import assert_frame_equal

from ricco.etl.transformer import round_by_columns
from ricco.etl.transformer import table2dict
from ricco.etl.transformer import drop_duplicates_by_order

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


def test_drop_duplicates_by_order():
  df_input = pd.DataFrame(
    {
      'a': [1, 1, 2, 2, 3],
      'b': ['Y', 'N', 'N', 'Y', 'N'],
    }
  )
  df_res = pd.DataFrame(
    {
      'a': [1, 2, 3],
      'b': ['Y', 'Y', 'N'],
    }
  )
  _df = drop_duplicates_by_order(df_input, 'a', col='b', order=['Y', 'N'])
  assert_frame_equal(_df, df_res)
