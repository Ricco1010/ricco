# -*-coding: GBK -*-
import ast

import pandas as pd
import requests
from ricco.coord_trans import BD2WGS
from ricco.util import reset2name
from tqdm import tqdm


def get_lnglat(addr: str,
               addr_type: str,
               city: str,
               key: str = None):
    '''
    根据地址获取经纬度

    :param addr: 地址
    :param addr_type: 地址的类型addr;地址 或 name：项目名称
    :param city: 城市
    :return:
    '''
    if key == None:
        key = 'csxAwMRuLWFnOm2gK6vrR30uyx7CSAjW'

    def get_address_bd(addr, city):
        url = f'http://api.map.baidu.com/geocoding/v3/?city={city}&address={addr}&output=json&ak={key}'
        return url

    def get_proj_bd(addr, city):
        url = f'http://api.map.baidu.com/place/v2/search?query={addr}&region={city}&city_limit=true&output=json&ak={key}'
        return url

    if addr_type == 'addr':
        address1 = get_address_bd(addr, city)
        res1 = requests.get(address1)
        j1 = ast.literal_eval(res1.text)
        name = None
        if 'result' in j1:
            if len(j1['result']) > 0:
                lng = j1['result']['location']['lng']
                lat = j1['result']['location']['lat']
            else:
                lng, lat = None, None
        else:
            lng, lat = None, None
    elif addr_type == 'name':
        address1 = get_proj_bd(addr, city)
        res1 = requests.get(address1)
        j1 = ast.literal_eval(res1.text)
        if 'results' in j1:
            if len(j1['results']) > 0:
                name = j1['results'][0]['name']
                lng = j1['results'][0]['location']['lng']
                lat = j1['results'][0]['location']['lat']
            else:
                name, lng, lat = None, None, None
        else:
            name, lng, lat = None, None, None
    else:
        raise ValueError("addr_type应为'addr'：地址 或 'name'：项目名称")
    return [lng, lat, name]


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
    if isinstance(addr_col, list):
        df['fake_address'] = ''
        for add in addr_col:
            df['fake_address'] = df['fake_address'].astype(str).str.cat(df[add].astype(str))
    else:
        df['fake_address'] = df[addr_col]

    if city_col == None:
        if city == None:
            raise KeyError('city和city_col不能同时为空')
        else:
            df['fake_city'] = city
    else:
        df['fake_city'] = df[city_col]
        if city != None:
            import warnings
            warnings.warn('city和city_col同时存在的情况下，优先使用city_col')

    prjct = df[~df['fake_city'].isna()][['fake_address', 'fake_city']].drop_duplicates()  # 避免重复解析
    prjct = prjct.reset_index(drop=True)
    empty = pd.DataFrame(columns=['fake_city', 'fake_address', 'lng', 'lat', '解析项目名'])

    for i in tqdm(prjct.index):
        lnglat = get_lnglat(addr=prjct['fake_address'][i],
                            addr_type=addr_type,
                            city=prjct['fake_city'][i],
                            key=key)
        add_df = pd.DataFrame({'fake_city': [prjct['fake_city'][i]],
                               'fake_address': [prjct['fake_address'][i]],
                               'lng': [lnglat[0]],
                               'lat': [lnglat[1]],
                               '解析项目名': [lnglat[2]]})
        empty = empty.append(add_df)

    df = df.merge(empty, how='left', on=['fake_city', 'fake_address'])
    df.drop(['fake_city', 'fake_address'], axis=1, inplace=True)
    df = BD2WGS(df)
    if 'name' not in df.columns:
        df = reset2name(df)
    return df
