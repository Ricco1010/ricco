__version__ = '0.1.27'

from ricco.Config import to_lnglat_dict
from ricco.gis_tools import circum_pio_num_geo_aoi
from ricco.gis_tools import mark_tags_df
from ricco.gis_tools import point_to_geom
from ricco.util import csv2shp
from ricco.util import ext
from ricco.util import extract_num
from ricco.util import fn
from ricco.util import fuzz_df
from ricco.util import fuzz_match
from ricco.util import mkdir_2
from ricco.util import pinyin
from ricco.util import rdf
from ricco.util import reset2name
from ricco.util import segment
from ricco.util import serise_to_float
from ricco.util import shp2csv
from ricco.util import split_csv
from ricco.util import to_csv_by_line
from ricco.util import to_float
from ricco.util import valid_check


def BD2WGS(df_org):
    from ricco.coord_trans import BD2WGS as _BD2WGS
    df_org = _BD2WGS(df_org)
    return df_org


def GD2WGS(df_org):
    from ricco.coord_trans import GD2WGS as _GD2WGS
    df_org = _GD2WGS(df_org)
    return df_org


def coord_trans_x2y(df_org, srs_from, srs_to):
    from ricco.coord_trans import coord_trans_x2y as _coord_trans_x2y
    df_org = _coord_trans_x2y(df_org, srs_from, srs_to)
    return df_org


def geocode_df(df,
               addr_col,
               addr_type: str,
               city: str = None,
               city_col: (str, list) = None,
               key=None):
    '''
    根据地址列或项目名称列解析经纬度

    :param df: 输入的Dataframe
    :param addr_col: 地址列，可以是多个列名组成的列表，有序的
    :param addr_type: 地址的类型addr;地址 或 name：项目名称
    :param city: 城市
    :return:
    '''
    from ricco.geocode_bd import geocode_df as _geocode_df
    df = _geocode_df(df, addr_col, addr_type, city, city_col, key)
    return df
