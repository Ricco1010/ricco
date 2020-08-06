import math
from enum import Enum
from functools import partial

import geojson.utils
import pandas as pd
import pyproj
from shapely import geos
from shapely import ops
from shapely import wkb
from shapely import wkt
from shapely.geometry import LineString
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry
from shapely.geometry.base import BaseMultipartGeometry
from shapely.ops import transform as sh_transform

"""
Dependencies:

pyproj==2.3.1
pandas==0.24.2
shapely[vectorized]==1.7a1
geojson==2.5.0
"""

__all__ = ['wgs2gcj', 'gcj2wgs', 'gcj2wgs_exact', 'distance', 'gcj2bd', 'bd2gcj', 'wgs2bd', 'bd2wgs']

earthR = 6378245.0
x_pi = math.pi * 3000.0 / 180.0
LNG_CHINA_RANGE = (72.004, 137.8347)
LAT_CHINA_RANGE = (0.8293, 55.8271)
LNG_RANGE = (-180, 180)
LAT_RANGE = (-90, 90)


class StrEnum(str, Enum):
    pass


class SRS(StrEnum):
    """空间参考系统(Spatial Reference System)"""
    #: 世界大地测量系统 (World Geodetic System 1984)
    wgs84 = 'wgs84'
    #: 百度坐标系
    bd09 = 'bd09'
    #: 国测局坐标（或火星坐标）
    gcj02 = 'gcj02'


def isnull(x):
    """determine whether input value is null, unlike pandas.isnull, this
    function only handles scalar value.

    null value includes None, pandas NaN/NaT
    """
    # pd.isnull will return array/list/frame for array/list/dataframe input, for
    # all those input, we considered is as not null
    result = pd.isnull(x)
    if not isinstance(result, bool):
        return False
    return result


def outOfChina(lat, lng):
    return not (72.004 <= lng <= 137.8347 and 0.8293 <= lat <= 55.8271)


def transform(x, y):
    xy = x * y
    absX = math.sqrt(abs(x))
    xPi = x * math.pi
    yPi = y * math.pi
    d = 20.0 * math.sin(6.0 * xPi) + 20.0 * math.sin(2.0 * xPi)

    lat = d
    lng = d

    lat += 20.0 * math.sin(yPi) + 40.0 * math.sin(yPi / 3.0)
    lng += 20.0 * math.sin(xPi) + 40.0 * math.sin(xPi / 3.0)

    lat += 160.0 * math.sin(yPi / 12.0) + 320 * math.sin(yPi / 30.0)
    lng += 150.0 * math.sin(xPi / 12.0) + 300.0 * math.sin(xPi / 30.0)

    lat *= 2.0 / 3.0
    lng *= 2.0 / 3.0

    lat += -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * xy + 0.2 * absX
    lng += 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * xy + 0.1 * absX

    return lat, lng


def delta(lat, lng):
    ee = 0.00669342162296594323
    dLat, dLng = transform(lng - 105.0, lat - 35.0)
    radLat = lat / 180.0 * math.pi
    magic = math.sin(radLat)
    magic = 1 - ee * magic * magic
    sqrtMagic = math.sqrt(magic)
    dLat = (dLat * 180.0) / ((earthR * (1 - ee)) / (magic * sqrtMagic) * math.pi)
    dLng = (dLng * 180.0) / (earthR / sqrtMagic * math.cos(radLat) * math.pi)
    return dLat, dLng


def wgs2gcj(wgsLat, wgsLng):
    if outOfChina(wgsLat, wgsLng):
        return wgsLat, wgsLng
    dlat, dlng = delta(wgsLat, wgsLng)
    return wgsLat + dlat, wgsLng + dlng


def gcj2wgs(gcjLat, gcjLng):
    if outOfChina(gcjLat, gcjLng):
        return gcjLat, gcjLng
    dlat, dlng = delta(gcjLat, gcjLng)
    return gcjLat - dlat, gcjLng - dlng


def gcj2wgs_exact(gcjLat, gcjLng):
    initDelta = 0.01
    threshold = 0.000001
    dLat = dLng = initDelta
    mLat = gcjLat - dLat
    mLng = gcjLng - dLng
    pLat = gcjLat + dLat
    pLng = gcjLng + dLng
    for _ in range(30):
        wgsLat = (mLat + pLat) / 2
        wgsLng = (mLng + pLng) / 2
        tmplat, tmplng = wgs2gcj(wgsLat, wgsLng)
        dLat = tmplat - gcjLat
        dLng = tmplng - gcjLng
        if abs(dLat) < threshold and abs(dLng) < threshold:
            return wgsLat, wgsLng
        if dLat > 0:
            pLat = wgsLat
        else:
            mLat = wgsLat
        if dLng > 0:
            pLng = wgsLng
        else:
            mLng = wgsLng
    return wgsLat, wgsLng


def distance(latA, lngA, latB, lngB):
    pi180 = math.pi / 180
    arcLatA = latA * pi180
    arcLatB = latB * pi180
    x = (math.cos(arcLatA) * math.cos(arcLatB)
         * math.cos((lngA - lngB) * pi180))
    y = math.sin(arcLatA) * math.sin(arcLatB)
    s = x + y
    if s > 1:
        s = 1
    if s < -1:
        s = -1
    alpha = math.acos(s)
    return alpha * earthR


def gcj2bd(gcjLat, gcjLng):
    if outOfChina(gcjLat, gcjLng):
        return gcjLat, gcjLng
    x = gcjLng
    y = gcjLat
    z = math.hypot(x, y) + 0.00002 * math.sin(y * x_pi)
    theta = math.atan2(y, x) + 0.000003 * math.cos(x * x_pi)
    bdLng = z * math.cos(theta) + 0.0065
    bdLat = z * math.sin(theta) + 0.006
    return bdLat, bdLng


def bd2gcj(bdLat, bdLng):
    if outOfChina(bdLat, bdLng):
        return bdLat, bdLng
    x = bdLng - 0.0065
    y = bdLat - 0.006
    z = math.hypot(x, y) - 0.00002 * math.sin(y * x_pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
    gcjLng = z * math.cos(theta)
    gcjLat = z * math.sin(theta)
    return gcjLat, gcjLng


def wgs2bd(wgsLat, wgsLng):
    return gcj2bd(*wgs2gcj(wgsLat, wgsLng))


def bd2wgs(bdLat, bdLng):
    return gcj2wgs(*bd2gcj(bdLat, bdLng))


_project_to_meter = partial(
    pyproj.transform,
    pyproj.Proj('epsg:4326'),
    pyproj.Proj('epsg:3857'))


def project_to_meter(geometry):
    """transform epsg:4326 to epsg:3857"""
    return ops.transform(_project_to_meter, geometry)


_project_to_lnglat = partial(
    pyproj.transform,
    pyproj.Proj('epsg:3857'),
    pyproj.Proj('epsg:4326'))


def project_to_lnglat(geometry):
    """transform epsg:3857 to epsg:4326"""
    return ops.transform(_project_to_lnglat, geometry)


def cut(line, dist):
    # Cuts a line in two at a distance from its starting point
    if dist <= 0.0 or dist >= line.length:
        return [LineString(line)]
    coords = list(line.coords)
    for i, p in enumerate(coords):
        pdist = line.project(Point(p))
        if pdist == dist:
            return [
                LineString(coords[:i + 1]),
                LineString(coords[i:])]
        if pdist > dist:
            cp = line.interpolate(dist)
            return [
                LineString(coords[:i] + [(cp.x, cp.y)]),
                LineString([(cp.x, cp.y)] + coords[i:])]


geos.WKBWriter.defaults['include_srid'] = True


def wkt_2_ewkb(geometry, srid=4326):
    geometry = wkt.loads(geometry)
    geos.lgeos.GEOSSetSRID(geometry._geom, srid)
    return geometry.wkb_hex


def wkb_2_ewkb(geometry, srid=4326):
    geometry = wkb.loads(geometry, hex=True)
    geos.lgeos.GEOSSetSRID(geometry._geom, srid)
    return geometry.wkb_hex


def geometry_2_ewkb(geometry, srid=4326):
    geos.lgeos.GEOSSetSRID(geometry._geom, srid)
    return geometry.wkb_hex


_fn_mapping = {
    (SRS.bd09, SRS.wgs84): bd2wgs,
    (SRS.gcj02, SRS.wgs84): gcj2wgs,
    (SRS.wgs84, SRS.bd09): wgs2bd,
    (SRS.gcj02, SRS.bd09): gcj2bd,
    (SRS.wgs84, SRS.gcj02): wgs2gcj,
    (SRS.bd09, SRS.gcj02): bd2gcj,
}


def coord_transform(lng: float, lat: float, from_srs: (SRS, str), to_srs: (SRS, str)):
    """坐标系转换

    :param lng: 输入的经度
    :param lat: 输入的纬度
    :param from_srs: 输入坐标的格式
    :param to_srs: 输出坐标的格式
    """
    if from_srs == to_srs:
        return lng, lat

    if isnull(lng) or isnull(lat):
        return None, None

    key = (from_srs, to_srs)
    if key not in _fn_mapping:
        raise NotImplementedError('not support transformation from %s to %s' % (from_srs, to_srs))
    lat, lng = _fn_mapping[key](lat, lng)
    return lng, lat


def coord_transform_geojson(obj: dict, from_srs: SRS, to_srs: SRS):
    """对GeoJSON格式内的所有坐标点执行坐标系转换

    Usage:
      from shapely.geometry import mapping
      from shapely.geometry import Point
      from shapely.geometry import shape

      point_bd09 = Point([1, 2])
      geojson = mapping(point_bd09)
      transformed = coord_transform(geojson, SRS.bd09, SRS.wgs84)
      point_wgs84 = shape(transformed)

    """
    return geojson.utils.map_tuples(lambda c: coord_transform(c[0], c[1], from_srs, to_srs), obj)


def coord_transform_geometry(geo: (BaseGeometry, BaseMultipartGeometry),
                             from_srs: SRS,
                             to_srs: SRS):
    """对Geomery内的所有点进行坐标转换，返回转换后的Geometry

    该方法可以支持所有的Shapely Geometry形状，包括Point, Line, Polygon,
    MultiPloygon等，返回的Geometry和输入的形状保持一致
    Args:
      geo: 输入的shapely Geometry
      from_srs: 输入的坐标格式
      to_srs: 输出的坐标格式
    Returns:
      转换后的shapely Geometry
    """
    return sh_transform(lambda x, y, z=None: coord_transform(x, y, from_srs, to_srs), geo)


def lnglat_check(df):
    if ('lng' not in df.columns) | ('lng' not in df.columns):
        raise KeyError('经纬度列名必须为lng和lat')


def coord_trans_x2y(df_org, srs_from: (SRS, str), srs_to: (SRS, str)):
    '''
    坐标批量转换工具

    :param df_org: 输入的dataframe，经纬度为lng和lat
    :param srs_from: 当前坐标系，可选'wgs84', 'bd09', 'gcj02'
    :param srs_to: 要转的坐标系，可选'wgs84', 'bd09', 'gcj02'
    :return:
    '''

    def fn(row):
        return coord_transform(row['lng'], row['lat'], srs_from, srs_to)

    lnglat_check(df_org)
    df_org['lng'] = df_org['lng'].astype(float)
    df_org['lat'] = df_org['lat'].astype(float)
    df_org[['lng', 'lat']] = df_org.apply(fn, axis=1, result_type='expand')
    print('坐标转换完成：%s → %s' % (srs_from, srs_to))
    return df_org


def BD2WGS(df_org):
    '''百度转WGS84'''
    df_org = coord_trans_x2y(df_org, SRS.bd09, SRS.wgs84)
    return df_org


def GD2WGS(df_org):
    '''高德转WGS84'''
    df_org = coord_trans_x2y(df_org, SRS.gcj02, SRS.wgs84)
    return df_org


def coord_trans_geom(df_org, srs_from: (SRS, str), srs_to: (SRS, str)):
    from shapely.wkb import loads, dumps
    if 'geometry' not in df_org.columns:
        raise KeyError('必须有geometry列')
    df_org['geometry'] = df_org['geometry'].apply(
        lambda x: dumps(coord_transform_geometry(loads(x,
                                                       hex=True),
                                                 srs_from,
                                                 srs_to),
                        hex=True,
                        srid=4326))
    print(f'坐标转换：{srs_from} --> {srs_to}')
    return df_org
