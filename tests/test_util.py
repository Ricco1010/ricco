import pandas as pd
from pandas.testing import assert_frame_equal

from ricco.util import col_round
from ricco.util import ensure_lnglat
from ricco.util import excel2date
from ricco.util import ext
from ricco.util import extract_num
from ricco.util import fn
from ricco.util import geom_wkb2lnglat
from ricco.util import geom_wkt2wkb
from ricco.util import house_type_format
from ricco.util import lnglat2geom
from ricco.util import pinyin
from ricco.util import reset2name
from ricco.util import segment
from ricco.util import to_float
from ricco.util import best_unique
from ricco.util import get_epsg


def test_getepsg():
    assert get_epsg('郑州') == 32649
    assert get_epsg('郑州市') == 32649
    assert get_epsg('一个没有的市') == 32651


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
    assert to_float('6.5%') == 0.065
    assert to_float('6.5%', ignore_pct=True) == 6.5
    assert to_float('p6.5%') == 0.065
    assert to_float('p6.5') == 6.5
    assert to_float('p6.5xx3.5', multi_warning=False) == 5.0
    assert to_float('p6.5xx3.5', rex_method='min', multi_warning=False) == 3.5
    assert to_float('p6.5xx3.5', rex_method='max', multi_warning=False) == 6.5
    assert to_float('p6.5xx3.5', rex_method='sum', multi_warning=False) == 10.0


def test_segment():
    assert segment(55, 20) == '40-60'
    assert segment(55, 20, sep='--', unit='米') == '40--60米'
    assert segment(55, [20]) == '20以上'
    assert segment(10, [20, 50], unit='米') == '20米以下'
    assert segment(20, [20, 50], unit='米') == '20-50米'
    assert segment(50, [20, 50], unit='米') == '50米以上'


def test_ensure_lnglat():
    df1 = pd.DataFrame({'经度': [131], '纬度': [31]})
    df2 = pd.DataFrame({'lng_WGS': [131], 'lat_WGS': [31]})
    df3 = pd.DataFrame({'lon_WGS': [131], 'lat_WGS': [31]})
    df4 = pd.DataFrame({'longitude': [131], 'latitude': [31]})
    df5 = pd.DataFrame({'lon': [131], 'lat': [31]})
    res = pd.DataFrame({'lng': [131], 'lat': [31]})
    assert_frame_equal(ensure_lnglat(df1), res)
    assert_frame_equal(ensure_lnglat(df2), res)
    assert_frame_equal(ensure_lnglat(df3), res)
    assert_frame_equal(ensure_lnglat(df4), res)
    assert_frame_equal(ensure_lnglat(df5), res)


def test_lnglat2geom():
    df = pd.DataFrame({'lng': [131],
                       'lat': [31]})
    res = pd.DataFrame({'lng': [131],
                        'lat': [31],
                        'geometry': ['010100000000000000006060400000000000003F40']})
    res_d = pd.DataFrame({'geometry': ['010100000000000000006060400000000000003F40']})
    assert_frame_equal(lnglat2geom(df, delete=True), res_d)
    assert_frame_equal(lnglat2geom(df, delete=False), res)


def test_geom_wkb2lnglat():
    df = pd.DataFrame({'geometry': ['010100000000000000006060400000000000003F40']})
    res = pd.DataFrame({'lng': [131.0],
                        'lat': [31.0],
                        'geometry': ['010100000000000000006060400000000000003F40']})
    res_d = pd.DataFrame({'lng': [131.0],
                          'lat': [31.0]})
    assert_frame_equal(geom_wkb2lnglat(df, delete=False), res, check_like=True)
    assert_frame_equal(geom_wkb2lnglat(df, delete=True), res_d, check_like=True)


def test_geom_wkt2wkb():
    df = pd.DataFrame({'geometry': ['POINT (131 31)']})
    res = pd.DataFrame({'geometry': ['0101000020E610000000000000006060400000000000003F40']})
    assert_frame_equal(geom_wkt2wkb(df), res)


def test_fn():
    assert fn('test_util.py') == 'test_util'


def test_ext():
    assert ext('test_util.py') == '.py'


def test_col_round():
    df = pd.DataFrame({'v': [12.12345, -0.23425, 0.12344, -14]})
    res = pd.DataFrame({'v': [12.12, -0.2343, 0.1234, -14.0]})
    assert_frame_equal(col_round(df, col=['v']), res)


def test_excel2date():
    assert excel2date('44146') == '2020-11-11'


def test_house_type_format():
    assert house_type_format('一室一厅') == '1房'
    assert house_type_format('两室一厅') == '2房'
    assert house_type_format('3室两厅') == '3房'
    assert house_type_format('4房1厅') == '4房'
    assert house_type_format('5室1厅') == '5房及以上'
    assert house_type_format('8室1厅') == '5房及以上'


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
    assert_frame_equal(best_unique(input_df,
                                   key_cols=['k'],
                                   value_cols=['v1', 'v2']),
                       res_df1)
    assert_frame_equal(best_unique(input_df,
                                   key_cols=['k'],
                                   value_cols=['v1', 'v2'],
                                   drop_if_null=None),
                       res_df2)
    assert_frame_equal(best_unique(input_df,
                                   key_cols=['k'],
                                   value_cols=['v1'],
                                   filter=True),
                       res_df3)
