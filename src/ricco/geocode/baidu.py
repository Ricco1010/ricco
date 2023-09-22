import warnings

import requests

from ..util.util import is_empty
from .util import DEFAULT_RES
from .util import MapKeys
from .util import MapUrls
from .util import error_baidu
from .util import fix_address
from .util import fix_city
from .util import gcj2xx
from .util import rv_score

KEY = MapKeys.baidu


def address_json(city: str, address: str, key=None):
  """百度地理编码接口"""
  if is_empty(address):
    return
  if not key:
    key = KEY
  url = f'{MapUrls.baidu}?city={city}&address={address}&output=json&ak={key}&ret_coordtype=gcj02ll'
  js = requests.get(url).json()
  error_baidu(js)
  if js['status'] == 0:
    return js['result']


def place_json(city: str, keywords: str, key=None):
  """百度地点检索接口"""
  if is_empty(keywords):
    return
  if not key:
    key = KEY
  url = f'{MapUrls.baidu_poi}?query={keywords}&region={city}&city_limit=true&output=json&ak={key}&ret_coordtype=gcj02ll'
  js = requests.get(url).json()
  error_baidu(js)
  if js['status'] == 0 and len(js['results']) >= 1:
    return js['results'][0]


def get_baidu(*,
              address,
              city,
              source,
              disable_cache=False,
              with_detail=True,
              key=None):
  """脉策geocode服务"""
  assert source in ('baidu', 'baidu_poi')
  if is_empty(address):
    return
  url = f'{MapUrls.mdt}?address={address}&city={city}&disable_cache={disable_cache}&with_detail={with_detail}&source={source}'
  req = requests.get(url)
  if req.status_code == 200:
    return req.json()['result'][0]['extra']
  if req.status_code in (400, 403):
    if source == 'baidu':
      return address_json(city=city, address=address, key=key)
    if source == 'baidu_poi':
      return place_json(city=city, keywords=address, key=key)
  else:
    warnings.warn(f'Unexpected status_code：{req.status_code}，{city}|{address}')


def get_address_baidu(city: str, address: str, srs='wgs84', key=None) -> dict:
  if is_empty(address):
    return DEFAULT_RES
  result = DEFAULT_RES.copy()
  source = 'baidu'
  city = fix_city(city)
  address = fix_address(address)
  address_dict = get_baidu(city=city, address=address, source=source, key=key)
  if address_dict:
    if address_dict['precise'] == 1:
      result['score'] = 100
    elif _score := address_dict.get('comprehension'):
      result['score'] = _score
    else:
      result['score'] = address_dict.get('confidence')
    latlng = gcj2xx(
        [address_dict['location']['lng'], address_dict['location']['lat']],
        srs=srs
    )
    result['lng'] = latlng[1]
    result['lat'] = latlng[0]
    result['source'] = source
  return result


def get_place_baidu(city: str, keywords: str, srs='wgs84', key=None) -> dict:
  if is_empty(keywords):
    return DEFAULT_RES
  result = DEFAULT_RES.copy()
  source = 'baidu_poi'
  city = fix_city(city)
  keywords = fix_address(keywords)
  poi_dict = get_baidu(city=city, address=keywords, source=source, key=key)
  if poi_dict:
    result['rv'] = poi_dict['name']
    latlng = gcj2xx(
        [poi_dict['location']['lng'], poi_dict['location']['lat']],
        srs=srs
    )
    result['lng'] = latlng[1]
    result['lat'] = latlng[0]
    result['score'] = rv_score(city, keywords, poi_dict['name'])
    result['source'] = source
  return result
