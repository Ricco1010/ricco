import csv
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.wkb import dumps
from shapely.wkb import loads

import pypinyin
import warnings
warnings.filterwarnings('ignore', 'Geometry is in a geographic CRS', UserWarning)
# 防止单个单元格文件过大而报错
maxInt = sys.maxsize
decrement = True
while decrement:
    decrement = False
    try:
        csv.field_size_limit(maxInt)
    except OverflowError:
        maxInt = int(maxInt / 10)
        decrement = True


def rdf(filepath):
    '''
    常用文件讀取方式
    :param filepath: 文件路徑
    :return: dataframe
    '''
    if '.csv' in filepath:
        try:
            df = pd.read_csv(filepath, engine='python', encoding='utf-8-sig')
        except:
            df = pd.read_csv(filepath, engine='python')
    elif '.xls' in filepath:
        df = pd.read_excel(filepath)
    else:
        raise Exception('未知文件格式')
    return df


def read_and_rename(file):
    col_dict = {'经度': 'lng', '纬度': 'lat', 'lon': 'lng', 'lng_WGS': 'lng', 'lat_WGS': 'lat', 'lon_WGS': 'lng',
                'longitude': 'lng', 'latitude': 'lat', "geom": "geometry"}
    df = rdf(file)
    df = df.rename(columns=col_dict)
    if 'lat' in df.columns:
        df.sort_values(['lat', 'lng'], inplace=True)
        df = df.reset_index(drop=True)
    return df


def pinyin(word):
    '''
    :param word:  中文字符串
    :return: 汉语拼音
    '''
    s = ''
    for i in pypinyin.pinyin(word, style=pypinyin.NORMAL):
        s += ''.join(i)
    return s


def shp2csv(shpfile_name):
    '''
    shapefile to csv
    :param shpfile_name: 文件路径
    :return: csv文件
    '''
    try:
        df = gpd.GeoDataFrame.from_file(shpfile_name, encoding='utf-8-sig')
    except:
        df = gpd.GeoDataFrame.from_file(shpfile_name, encoding='GBK')
    df['geometry'] = df['geometry'].apply(
        lambda x: dumps(x, hex=True, srid=4326))
    df.crs = 'epsg:4326'
    df.to_csv(shpfile_name.replace('.shp', '.csv'), encoding='utf-8-sig', index=0)


def csv2shp(filename):
    '''
    csv to shpfile
    :param filename: csv file path
    :return: shpfile
    '''
    df = rdf(filename)
    print(df.columns)
    print(df.head())
    df = df.rename(columns={'名称': 'name'})
    df = gpd.GeoDataFrame(df)
    df = df.rename(columns={'geom': 'geometry'})
    df['geometry'] = df['geometry'].apply(lambda x: loads(x, hex=True))
    df.crs = 'epsg:4326'
    try:
        df.to_file(filename.replace('.csv', '.shp'))
    except:
        df.columns = [pinyin(i) for i in df.columns]
        df.to_file(filename.replace('.csv', '.shp'), encoding='utf-8')
        print('已将列名转为汉语拼音进行转换')


def ensure_list(val):
    """将标量值和Collection类型都统一转换为LIST类型"""
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, (set, tuple)):
        return list(val)
    return [val]


def add(x, y):
    return x + y
