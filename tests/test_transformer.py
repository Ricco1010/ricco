import pandas as pd
from pandas.testing import assert_frame_equal

from ricco.etl.transformer import best_unique


def test_best_unique():
  input_df = pd.DataFrame({
    'k': ['s1', 's1', 's1', 's2', 's2', 's2', 's3', 's3', 's3'],
    'v1': [None, 's1', None, 's1', 's1', None, None, None, None],
    'v2': [None, 's2', 's2', None, None, 's2', None, None, None]
  })
  res_df1 = pd.DataFrame({
    'k': ['s2', 's1'],
    'v1': ['s1', 's1'],
    'v2': [None, 's2']
  })
  res_df2 = pd.DataFrame({
    'k': ['s3', 's2', 's1'],
    'v1': [None, 's1', 's1'],
    'v2': [None, None, 's2']
  })
  res_df3 = pd.DataFrame({
    'k': ['s1', 's2'],
    'v1': ['s1', 's1']
  })
  assert_frame_equal(
      best_unique(input_df,
                  key_cols=['k'],
                  value_cols=['v1', 'v2'],
                  drop_if_null='all'),
      res_df1
  )
  assert_frame_equal(
      best_unique(input_df,
                  key_cols=['k'],
                  value_cols=['v1', 'v2'],
                  drop_if_null=None),
      res_df2
  )
  assert_frame_equal(
      best_unique(input_df,
                  key_cols=['k'],
                  value_cols=['v1'],
                  filter=True,
                  drop_if_null='all'),
      res_df3
  )
