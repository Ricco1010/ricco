import pandas as pd

from ricco.etl.entropy import EntropyClass
from ricco.etl.entropy import entropy
from ricco.etl.entropy import rescale
from ricco.etl.entropy import standard_e
from ricco.etl.entropy import standard_e_neg


def test_standard_e():
  df = pd.DataFrame({
      'name': ['a', 'b', 'c'],
      'value_1': [1, 2, 3],
      'value_2': [-1, -2, -3],
  })
  assert min(list(standard_e(df, ['value_1'])['value_1'])) == 0
  assert max(list(standard_e(df, ['value_1'])['value_1'])) == 1
  assert list(standard_e(df, ['value_1'])['value_1']) == [0.0, 0.5, 1.0]
  assert list(standard_e(df, ['value_1'])['value_2']) == [-1, -2, -3]


def test_standard_e_neg():
  df = pd.DataFrame({
      'name': ['a', 'b', 'c'],
      'value_1': [1, 2, 3],
      'value_2': [-1, -2, -3],
  })
  assert min(list(standard_e_neg(df, ['value_2'])['value_2'])) == 0
  assert max(list(standard_e_neg(df, ['value_2'])['value_2'])) == 1
  assert list(standard_e_neg(df, ['value_2'])['value_2']) == [0.0, 0.5, 1.0]
  assert list(standard_e_neg(df, ['value_2'])['value_1']) == [1, 2, 3]


def test_entropy():
  df = pd.DataFrame({
      'name': ['a', 'b', 'c'],
      'value_1': [1, 2, 3],
      'value_2': [-1, -2, -3],
  })
  df_s = standard_e(df, ['value_1'])
  df_s = standard_e_neg(df_s, ['value_2'])
  x, weight = entropy(df_s, columns=['value_1', 'value_2'])
  assert weight['value_1'] == weight['value_2']
  assert list(x) == [0, 1 / 3, 2 / 3]


def test_rescale():
  df = pd.DataFrame({
      'name': ['a', 'b', 'c'],
      'value_1': [1, 2, 3],
      'value_2': [-1, -2, -3],
  })
  assert list(rescale(df, 'value_1')) == [0, 50, 100]
  assert max(rescale(df, 'value_1', score_range=(50, 70))) == 70
  assert min(rescale(df, 'value_1', score_range=(50, 70))) == 50
  assert min(rescale(df, 'value_2', score_range=(20, 30))) == 20
  assert max(rescale(df, 'value_2', score_range=(20, 30))) == 30
  assert min(rescale(df, 'value_1', score_range=(-20, 50))) == -20
  assert max(rescale(df, 'value_1', score_range=(-20, 50))) == 50


def test_EntropyClass():
  df = pd.DataFrame({
      'name': ['a', 'b', 'c'],
      'value_1': [1, 2, 3],
      'value_2': [-1, -2, -3],
  })
  Entropy = EntropyClass(df, ['value_1', 'value_2'], ['value_2'], '得分')
  assert list(Entropy.entropy_res) == [0, 1 / 3, 2 / 3]
  assert Entropy.entropy_weight['value_1'] == Entropy.entropy_weight['value_2']
  assert "得分" in Entropy.entropy_df.columns
  assert list(Entropy.entropy_df['得分']) == [0, 1 / 3, 2 / 3]
