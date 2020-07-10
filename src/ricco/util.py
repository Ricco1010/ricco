import csv
import os
import sys

import fiona
import geopandas as gpd
import pandas as pd
from shapely.wkb import dumps
from shapely.wkb import loads


def max_grid():
    '''防止单个单元格文件过大而报错'''
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
    max_grid()
    if os.path.splitext(filepath)[1] == '.csv':
        try:
            df = pd.read_csv(filepath, engine='python', encoding='utf-8-sig')
        except:
            df = pd.read_csv(filepath, engine='python')
    elif os.path.splitext(filepath)[1] == '.xls':
        df = pd.read_excel(filepath)
    elif os.path.splitext(filepath)[1] == '.xlsx':
        df = pd.read_excel(filepath)
    elif os.path.splitext(filepath)[1] == '.shp':
        try:
            df = gpd.GeoDataFrame.from_file(filepath, encoding='utf-8-sig')
        except UnicodeEncodeError:
            df = gpd.GeoDataFrame.from_file(filepath, encoding='GBK')
    else:
        raise Exception('未知文件格式')
    return df


def tofile(filename, encoding='GBK'):
    return filename


def to_csv_by_line(filename, data):
    with open(filename, 'a') as f:
        csv_write = csv.writer(f, dialect='excel')
        csv_write.writerow(data)


def read_and_rename(file):
    col_dict = {'经度': 'lng', '纬度': 'lat', 'lon': 'lng', 'lng_WGS': 'lng',
                'lat_WGS': 'lat', 'lon_WGS': 'lng',
                'longitude': 'lng', 'latitude': 'lat', "geom": "geometry"}
    df = rdf(file)
    df = df.rename(columns=col_dict)
    if 'lat' in df.columns:
        df.sort_values(['lat', 'lng'], inplace=True)
        df = df.reset_index(drop=True)
    return df


def reset2name(df):
    df = df.reset_index().rename(columns={'index': 'name'})
    return df


def pinyin(word):
    '''将中文转换为汉语拼音'''
    import pypinyin
    s = ''
    for i in pypinyin.pinyin(word, style=pypinyin.NORMAL):
        s += ''.join(i)
    return s


def mkdir_2(path):
    '''新建文件夹，忽略存在的文件夹'''
    if not os.path.isdir(path):
        os.makedirs(path)


def split_csv(filename, n=5):
    '''将文件拆分为多个同名文件，放置在与文件同名文件夹下的不同Part_文件夹中'''
    dir_name = os.path.splitext(os.path.basename(filename))[0]
    abs_path = os.getcwd()
    df = rdf(filename)
    t = len(df)
    p = int(t / n)
    for i in range(0, n):
        low = i * p
        high = (i + 1) * p
        dir_name2 = 'Part_' + str(i)
        save_path = os.path.join(abs_path, dir_name, dir_name2)
        savefile = os.path.join(save_path, filename)
        mkdir_2(save_path)
        if i == n - 1:
            add = df.iloc[low:, :]
        else:
            add = df.iloc[low: high, :]
        add.to_csv(savefile, index=0, encoding='utf-8')


def valid_check(df):
    '''检验面的有效性'''
    df['geometry'] = df['geometry'].apply(lambda x: loads(x, hex=True))
    df = gpd.GeoDataFrame(df)
    df.crs = 'epsg:4326'
    df['flag'] = df['geometry'].apply(lambda x: 1 if x.is_valid else -1)
    if len(df[df['flag'] < 0]) == 0:
        return ('success')
    else:
        raise Exception('有效性检验失败，请检查并修复面')


def shp2csv(shpfile_name):
    '''shapefile 转 csv 文件'''
    df = rdf(shpfile_name)
    df['geometry'] = df['geometry'].apply(lambda x: dumps(x, hex=True, srid=4326))
    df.crs = 'epsg:4326'
    save_path = os.path.splitext(shpfile_name)[0] + '.csv'
    df.to_csv(save_path, encoding='utf-8-sig', index=0)


def csv2shp(filename):
    '''csv文件 转 shapefile'''
    df = rdf(filename)
    df = df.rename(columns={'名称': 'name',
                            'geom': 'geometry'})
    df = gpd.GeoDataFrame(df)
    df['geometry'] = df['geometry'].apply(lambda x: loads(x, hex=True))
    df.crs = 'epsg:4326'
    save_path = os.path.splitext(filename)[0] + '.shp'
    try:
        df.to_file(save_path, encoding='utf-8')
    except fiona.errors.SchemaError:
        df.columns = [pinyin(i) for i in df.columns]
        df.to_file(save_path, encoding='utf-8')
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
