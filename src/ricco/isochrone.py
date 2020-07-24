import requests
from ricco import reset2name
from shapely import wkb
from shapely.geometry import shape
from tqdm import tqdm

mode_mapping = {'vehicle': 'driving',
                'walk': 'walking',
                'bike': 'cycling'}


def mpb_get_profile(mode):
    """mode in vehicle, bike, walk"""
    return f'mapbox/{mode_mapping[mode]}'


def mpb_get_coordinates(lng, lat):
    return f'{lng},{lat}'


def mpb_get_contours_minutes(second, divide_ratio=60, max_len=4, max_minute=60):
    """max 60 minutes, in increasing order"""
    if not isinstance(second, list):
        second = [second]
    round_list = [round(sec / divide_ratio) for sec in second]
    final_list = sorted(set(filter(lambda x: (x <= max_minute) & (x > 0), round_list)))
    cost_idx = []
    for min in round_list:
        if min in final_list:
            cost_idx.append(final_list.index(min))
        else:
            cost_idx.append(-1)
    minutes_list = [final_list[i:i + max_len] for i in range(0, len(final_list), max_len)]
    minutes_list = [','.join(map(str, min)) for min in minutes_list]
    return minutes_list, final_list, cost_idx


def mpb_iso_request(key, profile, coordinates, contours_minutes):
    base_path = 'https://api.mapbox.com'
    end_path = f'/isochrone/v1/{profile}/{coordinates}?contours_minutes={contours_minutes}'
    end_path += f'&polygons=true'
    end_path += f'&access_token={key}'
    api_return = requests.get(base_path + end_path).json()
    geom_list = [shape(feature['geometry']) for feature in api_return['features']]
    geom_list = [wkb.dumps(geom, hex=True, srid=4326) for geom in geom_list]
    geom_list.reverse()
    return geom_list


def isochrone(key, lng, lat, cost, mode='walk'):
    """cost可为一个list, mode可选 bike, walk, vehicle"""
    profile = mpb_get_profile(mode)
    coordinates = mpb_get_coordinates(lng, lat)
    minutes_list, _, cost_idx = mpb_get_contours_minutes(cost)
    geom_list = []
    for contours_minutes in minutes_list:
        geom_list += mpb_iso_request(key, profile, coordinates, contours_minutes)
    output_list = []
    for idx in cost_idx:
        if idx == -1:
            output_list.append(None)
        else:
            output_list.append(geom_list[idx])
    return output_list if len(output_list) > 1 else output_list[0]


class Config(object):
    # 每月更换一次key
    key = 'pk.eyJ1IjoicmljY28xMDEwIiwiYSI6ImNrY3k1bmVtNTA2a3kydGw3dWkzNXk2dDYifQ.d4RCEUKv4LDAAEqhgAFTzA'
    walk = 'walk'
    vehicle = 'vehicle'
    driving = 'vehicle'
    bike = 'bike'


def isochrone_df(df, cost, mode='walk'):
    df = reset2name(df)
    for i in tqdm(df.index):
        geom_list = isochrone(Config.key, df['lng'][i], df['lat'][i], cost, mode)
        if isinstance(cost, list):
            for j in range(len(cost)):
                df.loc[i, 'geometry' + str(cost[j])] = geom_list[j]
        elif isinstance(cost, int):
            df.loc[i, 'geometry'] = geom_list
    return df
