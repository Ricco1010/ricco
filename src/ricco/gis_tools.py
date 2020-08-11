import math
import os
import time
import warnings

import geopandas as gpd
import pandas as pd
from ricco.util import pinyin
from ricco.util import read_and_rename
from shapely.wkb import dumps
from shapely.wkb import loads
from tqdm import tqdm

warnings.filterwarnings('ignore', 'Geometry is in a geographic CRS', UserWarning)


def point_to_geo(df, lng, lat, delt=1):
    # from shapely.geometry import Point
    # df['geometry'] = gpd.GeoSeries(list(zip(df[lng], df[lat]))).apply(Point)  # 识别经纬度，转换点数据
    # df = gpd.GeoDataFrame(df)  # 转换Geodataframe格式
    from geopandas import points_from_xy
    df = gpd.GeoDataFrame(df, geometry=points_from_xy(df[lng], df[lat]))
    df.crs = 'epsg:4326'
    if delt == 1:
        del df[lng]
        del df[lat]
    return df


def city_epsgcode(city):
    citydict = {'上海': 32651, '南京': 32650, '合肥': 32650, '重庆': 32648, '宁波': 32651, '杭州': 32651, '济南': 32650, '沈阳': 32651,
                '广州': 32649, '北京': 32650, '昆明': 32648, '成都': 32648, '青岛': 32651, '长沙': 32649}
    if city in citydict:
        epsgcode = citydict[city]
    else:
        epsgcode = 32651
        warnings.warn("报错：target文件名不含城市名 or 城市不在 citydict 字典里，请补充; 目前默认投影坐标系为 WGS 84_UTM zone 51N")
    return epsgcode


def projection(gdf, code):
    '''投影'''
    gdf_prj = gdf.to_crs(epsg=code)
    return gdf_prj


def point_to_geom(df, lng, lat, delt=0):
    '''转为地理坐标'''
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[lng], df[lat]))
    gdf.crs = 'epsg:4326'  # 定义坐标系WGS84
    if delt == 1:
        del gdf[lng]
        del gdf[lat]
    return gdf


def geo_centroid(df, geom):
    '''获取中心点经纬度'''
    df[geom] = df[geom].apply(lambda x: loads(x, hex=True))
    df = gpd.GeoDataFrame(df, crs='epsg:4326')
    df["lng"] = df.centroid.x
    df["lat"] = df.centroid.y
    df[geom] = df[geom].apply(lambda x: dumps(x, hex=True))
    return df


def min_distance(point, lines):
    '''求最近距离'''
    return lines.distance(point).min()


def outformat(df, save_file, shp=0):
    if shp == 1:
        # df['geometry'] = df['geometry'].apply(lambda x: loads(x, hex=True))
        gdf = gpd.GeoDataFrame(df, crs='epsg:4326')
        try:
            gdf.to_file(save_file.replace('.csv', '.shp'), encoding='utf-8-sig')
        except:
            gdf.columns = [pinyin(i) for i in gdf.columns]
            gdf.to_file(save_file.replace('.csv', '.shp'), encoding='utf-8')
            print('已将列名转为汉语拼音进行转换')
        print('\n保存路径：', os.path.abspath(save_file.replace('.csv', '.shp')))
        gdf['geometry'] = gdf['geometry'].apply(lambda x: dumps(x, hex=True))
        df = pd.DataFrame(gdf)
    elif shp == 0:
        df = df.drop('geometry', axis=1)
    else:
        df['geometry'] = df['geometry'].apply(lambda x: dumps(x, hex=True))
    return df


def geom_center_point(file):
    df_target = read_and_rename(file)
    df_target = df_target.reset_index()
    df_target = geo_centroid(df_target, "geometry")
    df_target.to_csv(file)


def s_join_list(house_data_buffer, poi_data):
    spacial_join_result = gpd.sjoin(house_data_buffer, poi_data, how='right', op='intersects')
    merge_t = spacial_join_result.groupby(['order']).count()['key'].to_frame().reset_index().rename(
        columns={'key': 'counts'})
    merge_t = merge_t.loc[merge_t["counts"] > 0]
    return merge_t


def target_split_calc_list(gdf_target, df_poi, num_per_part, tcode, R=0):
    n_split = math.ceil(len(gdf_target) / num_per_part)
    print('\n数据将被拆成%s部分；' % n_split)
    lenth = len(gdf_target) / n_split
    print('每一部分约有%s行。\n' % int(lenth))
    modified = (R + 250) * 360 / 31544206
    joined_mt = pd.DataFrame()
    for i in tqdm(range(n_split)):
        # 数据行数最大最小值
        low = round(i * lenth)
        high = round(lenth * (i + 1))
        # 分割数据集
        gdf_part = gdf_target[(gdf_target.index >= low) & (gdf_target.index < high)]
        gdf_part = gdf_part.reset_index().drop('index', axis=1)
        bd = gdf_part.total_bounds
        # print('边界坐标：', bd)
        lng_min, lat_min, lng_max, lat_max = bd[0] - modified, bd[1] - modified, bd[2] + modified, bd[3] + modified
        # 根据边界经纬度删选POI数据
        df_poi_filter = df_poi[(df_poi['lng'] >= lng_min)
                               & (df_poi['lng'] <= lng_max)
                               & (df_poi['lat'] >= lat_min)
                               & (df_poi['lat'] <= lat_max)]
        df_poi_filter = pd.DataFrame(df_poi_filter).reset_index().drop('index', axis=1)
        if len(df_poi_filter) >= 1:
            # print('\nstep2：**********************格式转换***************************')
            if 'geometry' in df_poi_filter.columns:
                df_poi_filter["geometry"] = df_poi_filter["geometry"].apply(
                    lambda x: loads(x, hex=True))
                gdf_poi_filter = gpd.GeoDataFrame(df_poi_filter, crs='epsg:4326')
            else:
                gdf_poi_filter = point_to_geom(df_poi_filter, 'lng', 'lat')
            gdf_poi_filter = projection(gdf_poi_filter, tcode)
            gdf_part = projection(gdf_part, tcode)
            if R > 0:
                gdf_part["geometry"] = gdf_part.buffer(R)
            join_result = s_join_list(gdf_part, gdf_poi_filter)
        else:
            join_result = pd.DataFrame()
        joined_mt = joined_mt.append(join_result, sort=True)
        joined_mt = joined_mt.drop_duplicates()
    print('\n合并后表格：', joined_mt.shape)
    return joined_mt


def circum_pio_num_geo_aoilist(target, AOI, shp=0, num_per_part=150, R=0):
    '''
    :param target: 目标点、线、面面数据，csv文件，须有geometry字段；如果没有geometry，则自动利用经纬度（lng,lat）字段合成geometry
    :param AOI: 主要为栅格面数据和点数据设计，csv文件，须有geometry字段，或经纬度（lng,lat）字段
    :param shp: 是否生成shp文件，默认0不生成，并不含geometry，1则生成shp，其他则不生成shp, 但保留geometry
    '''
    start_all = time.perf_counter()
    print('AOI:', AOI)
    print('step1：读取数据.')
    tcity = os.path.splitext(os.path.basename(target))[0][:2]
    tcode = city_epsgcode(tcity)
    poi_name = os.path.splitext(os.path.basename(AOI))[0].split('_')[-1]
    save_file = os.path.basename(target).replace('.csv', '_' + poi_name + 'list.csv')
    if num_per_part == 0:
        if R == 0:
            num_per_part = 150
        else:
            num_per_part = 23000 - 5900 * (math.log10(R))

    df_target = read_and_rename(target)
    df_target = df_target.reset_index()
    df_target['key'] = 'point_' + df_target['index'].astype('str')
    # target 可以为点线面数据，所以统一用geometry字段计算
    if 'geometry' not in df_target.columns:
        df_target = point_to_geom(df_target, "lng", "lat")
    df_target = df_target[['key', 'geometry']]
    # df_poi 可以为点线面数据，所以统一用geometry字段计算，但用需要lng，lat字段筛选边界
    # 但目前df_poi主要为点，或250米栅格大小的数据
    df_poi = read_and_rename(AOI)
    if 'grid_id' not in df_poi.columns:
        df_poi = df_poi.rename(columns={"name": "grid_id", "名称": "grid_id"})
    df_poi = df_poi.reset_index().rename(columns={'index': 'order'})
    df_poi['order'] = df_poi['order'].astype('str')
    df_poi_grid = df_poi[['order', 'grid_id']]  # 预留数据
    if "lng" not in df_poi.columns:
        df_poi = geo_centroid(df_poi, "geometry")
    df_poi = df_poi[['lng', 'lat', "order", "geometry"]]
    print('step2：格式转换...')
    df_target['geometry'] = df_target['geometry'].apply(lambda x: loads(x, hex=True))
    gdf_target = gpd.GeoDataFrame(df_target)
    gdf_target.crs = 'epsg:4326'
    joined_mt = target_split_calc_list(gdf_target, df_poi, num_per_part, tcode, R)
    joined_mt.drop_duplicates(subset=["order"]).reset_index(drop=True)
    print('合并后表格：', joined_mt.shape)
    if joined_mt.empty:
        print("请注意：数据集为空")
        joined_mt.to_csv(save_file, encoding='utf-8-sig')
        return save_file
    buffer_result = df_poi.merge(joined_mt, on="order", how='right')
    buffer_result = buffer_result.merge(df_poi_grid, on="order", how='left').drop('order', axis=1)
    buffer_result = buffer_result.set_index('grid_id').rename(columns={'counts': poi_name + '_num'})
    buffer_result = outformat(buffer_result, save_file, shp)
    buffer_result = buffer_result.reset_index()
    buffer_result.to_csv(save_file, encoding='utf-8-sig')  # 保存成csv
    print('\n保存路径：', os.path.abspath(save_file))
    end_all = time.perf_counter()
    print('All process has finished. Run time is %s\n\n' % round(end_all - start_all, 2))
    return save_file


def s_join(house_data_buffer, poi_data, mode, var):
    house_data_buffer.crs = 'epsg:4326'
    poi_data.crs = 'epsg:4326'
    spacial_join_result = gpd.sjoin(house_data_buffer, poi_data, how='left', op='intersects')
    merge_t = spacial_join_result.groupby(['key']).count()['order'].to_frame().reset_index().rename(
        columns={'order': 'counts'})
    for mm in mode:
        if mm == 'sum':
            ss = spacial_join_result.groupby(['key'])[var].sum().reset_index()
        elif mm == 'mean':
            ss = spacial_join_result.groupby(['key'])[var].mean().reset_index()
        else:
            raise ValueError('mode错误,请选择sum或mean')
        ss.rename(columns={i: i + '_' + mm for i in var}, inplace=True)
        merge_t = merge_t.merge(ss)
    return merge_t


def target_split_calc(gdf_target, df_poi, num_per_part, tcode, mode, var, R=0):
    n_split = math.ceil(len(gdf_target) / num_per_part)
    print('\n数据将被拆成%s部分；' % n_split)
    lenth = len(gdf_target) / n_split
    print('每一部分约有%s行。\n' % int(lenth))
    modified = (R + 250) * 360 / 31544206
    # 以防poi面数据或线数据过大过长，增加一定的modified，暂定250，即栅格的长短
    joined_mt = pd.DataFrame()
    for i in tqdm(range(n_split)):
        # 数据行数最大最小值
        low = round(i * lenth)
        high = round(lenth * (i + 1))
        # 分割数据集
        gdf_part = gdf_target[(gdf_target.index >= low) & (gdf_target.index < high)]
        gdf_part = gdf_part.reset_index().drop('index', axis=1)
        bd = gdf_part.total_bounds
        # print('边界坐标：', bd)
        lng_min, lat_min, lng_max, lat_max = bd[0] - modified, bd[1] - modified, bd[2] + modified, bd[3] + modified
        # 根据边界经纬度删选POI数据
        df_poi_filter = df_poi[(df_poi['lng'] >= lng_min)
                               & (df_poi['lng'] <= lng_max)
                               & (df_poi['lat'] >= lat_min)
                               & (df_poi['lat'] <= lat_max)]
        df_poi_filter = pd.DataFrame(df_poi_filter).reset_index().drop('index', axis=1)
        if len(df_poi_filter) >= 1:
            # print('\nstep2：**********************格式转换***************************')
            if 'geometry' in df_poi_filter.columns:
                df_poi_filter["geometry"] = df_poi_filter["geometry"].apply(lambda x: loads(x, hex=True))
                gdf_poi_filter = gpd.GeoDataFrame(df_poi_filter, crs='epsg:4326')
            else:
                gdf_poi_filter = point_to_geom(df_poi_filter, 'lng', 'lat')  # 转换Geodataframe格式
            gdf_poi_filter = projection(gdf_poi_filter, tcode)
            gdf_part = projection(gdf_part, tcode)
            if R > 0:
                gdf_part["geometry"] = gdf_part.buffer(R)
            join_result = s_join(gdf_part, gdf_poi_filter, mode, var)
        else:
            join_result = pd.DataFrame(gdf_part['key'])
        joined_mt = joined_mt.append(join_result, sort=True)
    print('\n合并后表格：', joined_mt.shape)
    return joined_mt


def circum_pio_num_geo_aoi(target, POI, shp=0, mode=[], var=[], num_per_part=150, R=0):
    '''
    :param target: 目标面数据，csv文件，须有geometry字段；如果没有geometry，则自动利用经纬度合成geometry
    :param POI: 点数据csv文件，须有经纬度；如果没有经纬度，则自动利用geometry字段计算中心点
    :param shp: 是否生成shp文件，默认0不生成，并不含geometry，1则生成shp，其他则不生成shp, 但保留geometry
    :param mode: 可选sum，mean
    :param var: 计算mode的烈面，列表格式
    '''
    start_all = time.perf_counter()
    print('POI:', POI)
    print('step1：读取数据.')
    tcity = os.path.splitext(os.path.basename(target))[0][:2]
    tcode = city_epsgcode(tcity)
    poi_name = os.path.splitext(os.path.basename(POI))[0].split('_')[-1]
    if R > 0:
        save_file = 'r' + str(R) + '_' + os.path.basename(target).replace('.csv', '_' + poi_name + '.csv')
    else:
        save_file = os.path.basename(target).replace('.csv', '_' + poi_name + '.csv')
    if num_per_part == 0:
        if R == 0:
            num_per_part = 150
        else:
            num_per_part = 23000 - 5900 * (math.log10(R))
    df_target = read_and_rename(target)
    df_target = df_target.reset_index()
    df_target['key'] = 'point_' + df_target['index'].astype('str')
    if 'grid_id' not in df_target.columns:
        df_target = df_target.rename(columns={"name": "grid_id", "名称": "grid_id"})
    df_target_grid = df_target[['key', 'grid_id']]  # 预留数据
    if 'geometry' not in df_target.columns:
        df_target = point_to_geom(df_target, "lng", "lat")
    df_target = df_target[['key', 'geometry']]
    df_poi = read_and_rename(POI)
    if 'lat' not in df_poi.columns:
        df_poi = geo_centroid(df_poi, "geometry")
    if mode == []:
        df_poi = df_poi[['lng', 'lat']].reset_index().rename(columns={'index': 'order'})
    else:
        df_poi = df_poi[['lng', 'lat'] + var].reset_index().rename(columns={'index': 'order'})
    df_poi['order'] = df_poi['order'].astype('str')
    print('step2：格式转换...')
    df_target['geometry'] = df_target['geometry'].apply(lambda x: loads(x, hex=True))
    gdf_target = gpd.GeoDataFrame(df_target)
    gdf_target.crs = 'epsg:4326'
    joined_mt = target_split_calc(gdf_target, df_poi, num_per_part, tcode, mode, var, R)
    print('合并后表格：', joined_mt.shape)
    if joined_mt.empty:
        print("请注意：数据集为空")
        joined_mt.to_csv(save_file, encoding='utf-8-sig')
        return save_file

    df_target = df_target[['key', 'geometry']]
    buffer_result = df_target.merge(joined_mt, on='key', how='left')
    buffer_result = buffer_result.merge(df_target_grid, on='key', how='left').drop('key', axis=1)
    buffer_result["counts"] = buffer_result["counts"].fillna(0)
    buffer_result = buffer_result.set_index('grid_id').rename(columns={'counts': poi_name + '_num'})
    buffer_result = outformat(buffer_result, save_file, shp)
    buffer_result.to_csv(save_file, encoding='utf-8-sig')  # 保存成csv
    print('\n保存路径：', os.path.abspath(save_file))
    end_all = time.perf_counter()
    print('All process has finished. Run time is %s\n\n' % round(end_all - start_all, 2))
    return save_file


def nearest_neighbor(target, POI):
    # 近邻分析：离最近POI的距离
    print('POI:', POI)
    print('step1：读取数据.')

    tcity = os.path.splitext(os.path.basename(target))[0][:2]
    tcode = city_epsgcode(tcity)
    poi_name = os.path.splitext(os.path.basename(POI))[0].split('_')[-1]
    save_file = target.replace('.csv', '_nearest_') + poi_name + ".csv"
    df_target = read_and_rename(target)
    df_poi = read_and_rename(POI)
    print('step2：格式转换...')
    gdf_target = point_to_geom(df_target, 'lng', 'lat')  # 转换Geodataframe格式
    gdf_poi = point_to_geom(df_poi, 'lng', 'lat')  # 转换Geodataframe格式
    print('step3：投影..........')
    gdf_target = projection(gdf_target, tcode)
    gdf_poi = projection(gdf_poi, tcode)
    v_name = 'near_%s_dist' % poi_name
    print('step4：近邻分析........')
    gdf_target[v_name] = gdf_target.geometry.apply(lambda x: min_distance(x, gdf_poi))
    df_target = outformat(gdf_target, save_file)
    df_target.to_csv(save_file, encoding='utf-8-sig', index=False)
    print('All process has finished.')
    return save_file


def nearest_neighbor_csv_geo(target, POI, shp=0):
    # 近邻分析：离最近POI的距离
    tcity = os.path.splitext(os.path.basename(target))[0][:2]
    tcode = city_epsgcode(tcity)
    poi_name = os.path.splitext(os.path.basename(POI))[0].split('_')[-1]
    print('step1：读取数据.')
    df_target = read_and_rename(target)
    df_poi = read_and_rename(POI)
    print('step2：格式转换...')
    if 'lat' not in df_target.columns:
        df_target = geo_centroid(df_target, "geometry")
    gdf_target = point_to_geom(df_target, 'lng', 'lat')  # 转换Geodataframe格式

    df_poi['geometry'] = df_poi['geometry'].apply(lambda x: loads(x, hex=True))
    gdf_poi = gpd.GeoDataFrame(df_poi)
    gdf_poi.crs = 'epsg:4326'

    print('step3：投影..........')
    gdf_target = projection(gdf_target, tcode)
    gdf_poi = projection(gdf_poi, tcode)
    v_name = 'near_%s_dist' % poi_name
    print('step4：近邻分析........')
    gdf_target[v_name] = gdf_target.geometry.apply(lambda x: min_distance(x, gdf_poi))

    save_file = target.replace('.csv', '_nearest_') + poi_name + ".csv"
    df_target = outformat(gdf_target, save_file, shp)
    df_target.to_csv(save_file, encoding='utf-8-sig', index=False)
    print('All process has finished.')
    return save_file


def mark_tags_df(point_df: pd.DataFrame, polygon_df: pd.DataFrame, col_list: list = None):
    '''
    :param point_df: dataframe 点文件，需要有经纬度或geometry
    :param polygon_df: dataframe 面文件，需要有geometry
    :param col_list: 面文件中的列名，需要连接到点文件后面的
    :return:
    '''
    from ricco import to_lnglat_dict
    from ricco.util import ensure_list
    col_list = ensure_list(col_list)

    def split_df(df: pd.DataFrame, column='geometry'):
        df = df.reset_index().rename(columns={'index': 'uid'})
        df_null = df[df[column].isna()].reset_index(drop=True)
        df_not_null = df[~df[column].isna()].reset_index(drop=True)
        return df_null, df_not_null

    point_df = point_df.rename(columns=to_lnglat_dict)
    for i in col_list:
        point_df.rename(columns={i: str(i) + '_origin'}, inplace=True)

    if ('lng' in point_df.columns) & ('lat' in point_df.columns):
        point_df_null, point_df_ = split_df(point_df, 'lng')
        point_df_ = point_to_geo(point_df_, 'lng', 'lat', delt=0)
        point_df_null = point_df_null.drop(['lng', 'lat'], axis=1)
    elif 'geometry' in point_df.columns:
        point_df_null, point_df_ = split_df(point_df, 'geometry')
        point_df_['geometry'] = point_df_['geometry'].apply(lambda x: loads(x, hex=True))
        point_df_ = gpd.GeoDataFrame(point_df_)
        point_df_null = point_df_null.drop('geometry', axis=1)
    else:
        raise KeyError('点文件中必须有经纬度或geometry')

    if col_list != None:
        polygon_df = polygon_df[col_list + ['geometry']]

    point_df_ = point_df_.reset_index(drop=True)
    polygon_df = polygon_df.reset_index(drop=True)
    polygon_df['geometry'] = polygon_df['geometry'].apply(lambda x: loads(x, hex=True))
    polygon_df = gpd.GeoDataFrame(polygon_df)
    polygon_df.crs, point_df_.crs = 'epsg:4326', 'epsg:4326'

    final_file = gpd.sjoin(point_df_,
                           polygon_df,
                           how='left',
                           op='intersects').drop('index_right', axis=1)
    final_file = final_file.append(point_df_null,
                                   sort=False)
    final_file = final_file.drop('geometry',
                                 axis=1).sort_values('uid').set_index('uid')
    return final_file
