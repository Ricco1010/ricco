# -*-coding: GBK -*-
import ast

import pandas as pd
import requests
from tqdm import tqdm

from ricco.coord_trans import BD2WGS
from ricco.util import reset2name


def get_lnglat(addr: str,
               addr_type: str,
               city: str):
    '''
    根据地址获取经纬度

    :param addr: 地址
    :param addr_type: 地址的类型addr;地址 或 name：项目名称
    :param city: 城市
    :return:
    '''

    def get_address_bd(keywords, city):
        key = 'csxAwMRuLWFnOm2gK6vrR30uyx7CSAjW'
        basic_ads = 'http://api.map.baidu.com/geocoding/v3/?city={}&address={}&output=json&ak={}'
        address = basic_ads.format(city, keywords, key)
        return address

    def get_proj_bd(keywords, city):
        key = 'csxAwMRuLWFnOm2gK6vrR30uyx7CSAjW'
        basic_ads = 'http://api.map.baidu.com/place/v2/search?query={}&region={}&city_limit=true&output=json&ak={}'
        address = basic_ads.format(keywords, city, key)
        return address

    keywords = city + '' + addr
    if addr_type == 'addr':
        address1 = get_address_bd(keywords, city)
        res1 = requests.get(address1)
        j1 = ast.literal_eval(res1.text)
        name = None
        if len(j1['result']) > 0:
            lng = j1['result']['location']['lng']
            lat = j1['result']['location']['lat']
        else:
            lng, lat = None, None
    elif addr_type == 'name':
        address1 = get_proj_bd(keywords, city)
        res1 = requests.get(address1)
        j1 = ast.literal_eval(res1.text)
        if len(j1['results']) > 0:
            name = j1['results'][0]['name']
            lng = j1['results'][0]['location']['lng']
            lat = j1['results'][0]['location']['lat']
        else:
            name, lng, lat = None, None, None
    else:
        raise ValueError("addr_type应为'addr'：地址 或 'name'：项目名称")
    return [lng, lat, name]


def geocode_df(df,
               addr_col,
               addr_type: str,
               city: str = ''):
    '''
    根据地址列或项目名称列解析经纬度

    :param df: 输入的Dataframe
    :param addr_col: 地址列，可以是多个列名组成的列表，有序的
    :param addr_type: 地址的类型addr;地址 或 name：项目名称
    :param city: 城市
    :return:
    '''
    if isinstance(addr_col, list):
        addr_m = 'merge_address'
        df[addr_m] = ''
        for add in addr_col:
            df[addr_m] = df[addr_m].astype(str).str.cat(df[add].astype(str))
    else:
        addr_m = addr_col

    prjct = df[addr_m].drop_duplicates()  # 避免重复解析
    empty = pd.DataFrame(columns=[addr_m, 'lng', 'lat', '解析项目名'])
    for i in tqdm(prjct):
        lnglat = get_lnglat(i, addr_type, city)
        add_df = pd.DataFrame({addr_m: [i],
                               'lng': [lnglat[0]],
                               'lat': [lnglat[1]],
                               '解析项目名': [lnglat[2]]})
        empty = empty.append(add_df)
    df = df.merge(empty, how='left', on=addr_m)
    if isinstance(addr_col, list):
        df.drop(addr_m, axis=1, inplace=True)
    df = BD2WGS(df)
    if 'name' not in df.columns:
        df = reset2name(df)
    return df
