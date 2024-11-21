import warnings

import requests

from ..util.decorator import check_null
from .util import DEFAULT_RES
from .util import MapKeys
from .util import MapUrls
from .util import error_baidu
from .util import fix_address
from .util import fix_city
from .util import gcj2xx
from .util import rv_score

KEY = MapKeys.baidu


@check_null()
def address_json(address: str, city: str, key=None):
  """百度地理编码接口"""
  if not key:
    key = KEY
  url = f'{MapUrls.baidu}?city={city}&address={address}&output=json&ak={key}&ret_coordtype=gcj02ll'
  js = requests.get(url).json()
  error_baidu(js)
  if js['status'] == 0:
    return js['result']


@check_null()
def place_json(address: str, city: str, key=None):
  """百度地点检索接口"""
  if not key:
    key = KEY
  url = f'{MapUrls.baidu_poi}?query={address}&region={city}&city_limit=true&output=json&ak={key}&ret_coordtype=gcj02ll'
  js = requests.get(url).json()
  error_baidu(js)
  if js['status'] == 0 and len(js['results']) >= 1:
    return js['results'][0]


@check_null()
def get_baidu(*,
              address,
              city,
              source,
              disable_cache=False,
              with_detail=True,
              key=None):
  """MC geocode服务"""
  assert source in ('baidu', 'baidu_poi')
  url = f'{MapUrls.mdt}?address={address}&city={city}&disable_cache={disable_cache}&with_detail={with_detail}&source={source}'
  if key:
    url += f'&key={key}'
  req = requests.get(url)
  if req.status_code == 200:
    return req.json()['result'][0]['extra']
  if req.status_code in (400, 403):
    if source == 'baidu':
      return address_json(address=address, city=city, key=key)
    if source == 'baidu_poi':
      return place_json(address=address, city=city, key=key)
  else:
    warnings.warn(f'Unexpected status_code：{req.status_code}，{city}|{address}')


@check_null(default_rv=DEFAULT_RES)
def get_address_baidu(address: str, city: str, srs='wgs84', key=None) -> dict:
  result = DEFAULT_RES.copy()
  source = 'baidu'
  city = fix_city(city)
  address = fix_address(address)
  address_dict = get_baidu(address=address, city=city, source=source, key=key)
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


@check_null(default_rv=DEFAULT_RES)
def get_place_baidu(address: str, city: str, srs='wgs84', key=None) -> dict:
  result = DEFAULT_RES.copy()
  source = 'baidu_poi'
  city = fix_city(city)
  address = fix_address(address)
  poi_dict = get_baidu(address=address, city=city, source=source, key=key)
  if poi_dict:
    result['rv'] = poi_dict['name']
    latlng = gcj2xx(
        [poi_dict['location']['lng'], poi_dict['location']['lat']],
        srs=srs
    )
    result['lng'] = latlng[1]
    result['lat'] = latlng[0]
    result['score'] = rv_score(city, address, poi_dict['name'])
    result['source'] = source
  return result
