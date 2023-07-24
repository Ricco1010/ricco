import logging

import requests

from ..util.util import is_empty
from .util import MapKeys
from .util import MapUrls
from .util import error_amap
from .util import fix_address
from .util import gcj2xx
from .util import rv_score

KEY = MapKeys.amap


def address_json(city: str, address: str, key=None):
  """高德地理编码接口"""
  if is_empty(address):
    return None
  if not key:
    key = KEY
  url = f'{MapUrls.amap}?address={address}&city={city}&key={key}'
  js = requests.get(url).json()
  error_amap(js)
  if js['status'] == '1' and int(js['count']) >= 1:
    return js['geocodes'][0]
  return None


def place_json(city: str, keywords: str, key=None):
  """高德地点检索接口"""
  if is_empty(keywords):
    return None
  if not key:
    key = KEY
  url = f'{MapUrls.amap_poi}?keywords={keywords}&city={city}&key={key}'
  js = requests.get(url).json()
  error_amap(js)
  if js['status'] == '1' and int(js['count']) >= 1:
    return js['pois'][0]
  return None


def get_amap(*,
             address,
             city,
             source,
             with_detail=True,
             disable_cache=False,
             key=None):
  """脉策geocode服务"""
  if is_empty(address):
    return None
  url = f'{MapUrls.mdt}?address={address}&city={city}&disable_cache={disable_cache}&with_detail={with_detail}&source={source}'
  req = requests.get(url)
  if req.status_code == 200:
    try:
      return req.json()['result'][0]['extra']
    except Exception as e:
      logging.warning(f'{e}，{req}')
      return None
  elif req.status_code in (400, 403):
    if source == 'amap':
      return address_json(city=city, address=address, key=key)
    elif source == 'amap_poi':
      return place_json(city=city, keywords=address, key=key)
    else:
      raise ValueError('source参数错误')
  else:
    return None


def get_address_amap(city: str, address: str, srs: str = 'wgs84', key=None):
  if is_empty(address):
    return {
      'rv': None,
      'score': 0,
      'lng': None,
      'lat': None,
    }
  city = city.rstrip('市')
  address = fix_address(address).replace('|', '')
  address_dict = get_amap(city=city, address=address, source='amap', key=key)
  if address_dict:
    rv = address_dict['formatted_address']
    lnglat = address_dict['location'].split(',')
    latlng = gcj2xx(lnglat, srs=srs)
    lng = latlng[1]
    lat = latlng[0]
  else:
    rv, lng, lat = None, None, None
  return {
    'rv': rv,
    'score': 0,
    'lng': lng,
    'lat': lat,
  }


def get_place_amap(city: str, keywords: str, srs='wgs84', key=None):
  if is_empty(keywords):
    return {
      'rv': None,
      'score': 0,
      'lng': None,
      'lat': None,
    }
  city = city.rstrip('市')
  keywords = fix_address(keywords)
  res = get_amap(city=city, address=keywords, source='amap_poi', key=key)
  if res:
    rv = res['name']
    lnglat = res['location'].split(',')
    latlng = gcj2xx(lnglat, srs=srs)
    lng = latlng[1]
    lat = latlng[0]
    score = rv_score(city, keywords, rv)
  else:
    rv, lng, lat, score = None, None, None, 0
  return {
    'rv': rv,
    'score': score,
    'lng': lng,
    'lat': lat,
  }
