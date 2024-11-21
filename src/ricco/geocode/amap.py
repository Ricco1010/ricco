import warnings

import requests

from ..util.decorator import check_null
from .util import DEFAULT_RES
from .util import MapKeys
from .util import MapUrls
from .util import error_amap
from .util import fix_address
from .util import fix_city
from .util import gcj2xx
from .util import rv_score

KEY = MapKeys.amap


@check_null()
def address_json(address: str, city: str, key=None):
  """高德地理编码接口"""
  if not key:
    key = KEY
  url = f'{MapUrls.amap}?address={address}&city={city}&key={key}'
  js = requests.get(url).json()
  error_amap(js)
  if js['status'] == '1' and int(js['count']) >= 1:
    return js['geocodes'][0]


@check_null()
def place_json(address: str, city: str, key=None):
  """高德地点检索接口"""
  if not key:
    key = KEY
  url = f'{MapUrls.amap_poi}?keywords={address}&city={city}&key={key}'
  js = requests.get(url).json()
  error_amap(js)
  if js['status'] == '1' and int(js['count']) >= 1:
    return js['pois'][0]


@check_null()
def get_amap(*,
             address,
             city,
             source,
             with_detail=True,
             disable_cache=False,
             key=None):
  """MC geocode服务"""
  assert source in ('amap', 'amap_poi')
  url = f'{MapUrls.mdt}?address={address}&city={city}&disable_cache={disable_cache}&with_detail={with_detail}&source={source}'
  if key:
    url += f'&key={key}'
  req = requests.get(url)
  if req.status_code == 200:
    try:
      return req.json()['result'][0]['extra']
    except Exception as e:
      warnings.warn(f'{e}，{req}')
      return
  if req.status_code in (400, 403):
    if source == 'amap':
      return address_json(address=address, city=city, key=key)
    if source == 'amap_poi':
      return place_json(address=address, city=city, key=key)
  else:
    warnings.warn(f'Unexpected status_code：{req.status_code}，{city}|{address}')


@check_null(default_rv=DEFAULT_RES)
def get_address_amap(address: str, city: str,
                     srs: str = 'wgs84', key=None) -> dict:
  result = DEFAULT_RES.copy()
  source = 'amap'
  city = fix_city(city)
  address = fix_address(address)
  address_dict = get_amap(address=address, city=city, source=source, key=key)
  if address_dict:
    result['rv'] = address_dict['formatted_address']
    latlng = gcj2xx(address_dict['location'].split(','), srs=srs)
    result['lng'] = latlng[1]
    result['lat'] = latlng[0]
    result['score'] = rv_score(city, address, address_dict['formatted_address'])
    result['source'] = source
  return result


@check_null(default_rv=DEFAULT_RES)
def get_place_amap(address: str, city: str,
                   srs: str = 'wgs84', key=None) -> dict:
  result = DEFAULT_RES.copy()
  source = 'amap_poi'
  city = fix_city(city)
  address = fix_address(address)
  poi_dict = get_amap(address=address, city=city, source='amap_poi', key=key)
  if poi_dict:
    result['rv'] = poi_dict['name']
    latlng = gcj2xx(poi_dict['location'].split(','), srs=srs)
    result['lng'] = latlng[1]
    result['lat'] = latlng[0]
    result['score'] = rv_score(city, address, poi_dict['name'])
    result['source'] = source
  return result
