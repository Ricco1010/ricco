import pandas as pd
import pytest

from ricco.util.assertion import assert_columns_exists
from ricco.util.assertion import assert_not_empty_str
from ricco.util.assertion import assert_not_null
from ricco.util.assertion import assert_series_digit
from ricco.util.assertion import assert_series_unique
from ricco.util.assertion import assert_subset
from ricco.util.assertion import assert_values_in
from ricco.util.assertion import skip_column


def test_skip_column():
  df = pd.DataFrame({'a': [1], 'b': [2]})
  assert skip_column(df, 'a') is False
  assert skip_column(df, 'c') is True
  with pytest.raises(KeyError):
    skip_column(df, 'c', skip_if_not_exists=False)


def test_assert_columns_exists():
  df = pd.DataFrame({'a': [1], 'b': [2]})
  assert_columns_exists(df, ['a', 'b'])
  with pytest.raises(AssertionError):
    assert_columns_exists(df, ['a', 'c'])


def test_assert_not_empty_str():
  df = pd.DataFrame({'a': ['x', 'y']})
  assert_not_empty_str(df, 'a')
  df2 = pd.DataFrame({'a': ['x', '']})
  with pytest.raises(AssertionError):
    assert_not_empty_str(df2, 'a')


def test_assert_not_null():
  df = pd.DataFrame({'a': [1, 2, 3]})
  assert_not_null(df, 'a')
  df2 = pd.DataFrame({'a': [1, None, 3]})
  with pytest.raises(AssertionError):
    assert_not_null(df2, 'a')


def test_assert_values_in():
  df = pd.DataFrame({'a': ['x', 'y']})
  assert_values_in(df, 'a', ['x', 'y', 'z'])
  with pytest.raises(AssertionError):
    assert_values_in(df, 'a', ['x'])
  df2 = pd.DataFrame({'a': ['x', 'y']})
  assert_values_in(df2, 'a', {'k1': 'x', 'k2': 'y'})


def test_assert_series_unique():
  df = pd.DataFrame({'a': [1, 2, 3]})
  assert_series_unique(df, 'a')
  df2 = pd.DataFrame({'a': [1, 1, 2]})
  with pytest.raises(AssertionError):
    assert_series_unique(df2, 'a')


def test_assert_series_digit():
  df = pd.DataFrame({'a': [1, 2, 3]})
  assert_series_digit(df, 'a')
  df2 = pd.DataFrame({'a': ['1', '2', 'abc']})
  with pytest.raises(AssertionError):
    assert_series_digit(df2, 'a')


def test_assert_subset():
  assert_subset([1, 2], [1, 2, 3])
  with pytest.raises(AssertionError):
    assert_subset([1, 4], [1, 2, 3])
