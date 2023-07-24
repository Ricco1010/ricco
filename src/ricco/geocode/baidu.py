import requests

from ..util.util import is_empty
from .util import MapKeys
from .util import MapUrls
from .util import error_baidu
from .util import fix_address
from .util import gcj2xx
from .util import rv_score

KEY = MapKeys.baidu


def address_json(city: str, address: str, key=None):
  """百度地理编码接口"""
  if is_empty(address):
    return None
  if not key:
    key = KEY
  url = f'{MapUrls.baidu}?city={city}&address={address}&output=json&ak={key}&ret_coordtype=gcj02ll'
  js = requests.get(url).json()
  error_baidu(js)
  if js['status'] == 0:
    return js['result']
  return None


def place_json(city: str, keywords: str, key=None):
  """百度地点检索接口"""
  if is_empty(keywords):
    return None
  if not key:
    key = KEY
  url = f'{MapUrls.baidu_poi}?query={keywords}&region={city}&city_limit=true&output=json&ak={key}&ret_coordtype=gcj02ll'
  js = requests.get(url).json()
  error_baidu(js)
  if js['status'] == 0 and len(js['results']) >= 1:
    return js['results'][0]
  return None


def get_baidu(*,
              address,
              city,
              source,
              disable_cache=False,
              with_detail=True,
              key=None):
  """脉策geocode服务"""
  if is_empty(address):
    return None
  url = f'{MapUrls.mdt}?address={address}&city={city}&disable_cache={disable_cache}&with_detail={with_detail}&source={source}'
  req = requests.get(url)
  if req.status_code == 200:
    return req.json()['result'][0]['extra']
  elif req.status_code in (400, 403):
    if source == 'baidu':
      return address_json(city=city, address=address, key=key)
    elif source == 'baidu_poi':
      return place_json(city=city, keywords=address, key=key)
    else:
      raise ValueError('source参数错误')
  else:
    return None


def get_address_baidu(city: str, address: str, srs='wgs84', key=None):
  if is_empty(address):
    return {
      'rv': None,
      'score': 0,
      'lng': None,
      'lat': None,
    }
  city = city.rstrip('市')
  address = fix_address(address)
  res = get_baidu(city=city, address=address, source='baidu', key=key)
  if res:
    lnglat = [res['location']['lng'], res['location']['lat']]
    if res['precise'] == 1:
      score = 100
    else:
      score = res.get('comprehension') if res.get('comprehension') else res.get(
          'confidence')
    latlng = gcj2xx(lnglat, srs=srs)
    lng = latlng[1]
    lat = latlng[0]
  else:
    score, lng, lat = 0, None, None
  return {
    'rv': None,
    'score': score,
    'lng': lng,
    'lat': lat,
  }


def get_place_baidu(city: str, keywords: str, srs='wgs84', key=None):
  if is_empty(keywords):
    return {
      'rv': None,
      'score': 0,
      'lng': None,
      'lat': None,
    }
  city = city.rstrip('市')
  keywords = fix_address(keywords)
  res = get_baidu(city=city, address=keywords, source='baidu_poi', key=key)
  if res:
    rv = res['name']
    lnglat = [res['location']['lng'], res['location']['lat']]
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
