#-*-coding: GBK -*-
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from ricco.util import add
from ricco.util import extract_num
from ricco.util import pinyin
from ricco.util import reset2name
from ricco.util import to_float


def test_add():
    assert add(1, 1) == 2


def test_pinyin():
    assert pinyin('测试') == 'ceshi'
    assert pinyin('test') == 'test'


def test_reset2name():
    inp = pd.DataFrame({'a': [1, 2, 3]})
    oup = pd.DataFrame({'name': [0, 1, 2], 'a': [1, 2, 3]})
    assert_frame_equal(reset2name(inp), oup)


def test_extract_num():
    string = 'fo13--;gr35.3'
    assert extract_num(string) == ['13', '35.3']
    assert extract_num(string, num_type='int') == [13, 35]
    assert extract_num(string, num_type='float') == [13.0, 35.3]
    assert extract_num(string, num_type='str', join_list=True) == '1335.3'


def test_to_float():
    assert to_float('6.5') == 6.5
    assert to_float('p6.5', rex=True, rex_warning=False) == 6.5
    assert to_float('p6.5xx3.5', rex=True, rex_warning=False) == 5.0
    assert to_float('p6.5xx3.5', rex=True, rex_method='min', rex_warning=False) == 3.5
    assert to_float('p6.5xx3.5', rex=True, rex_method='max', rex_warning=False) == 6.5
    assert to_float('p6.5xx3.5', rex=True, rex_method='sum', rex_warning=False) == 10.0
