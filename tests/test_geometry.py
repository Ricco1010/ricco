import warnings

import pandas as pd
from pandas.testing import assert_frame_equal
from shapely.geometry import MultiPolygon
from shapely.geometry import Point
from shapely.geometry import Polygon

from ricco.geometry.df import mark_tags_v2
from ricco.geometry.util import get_epsg
from ricco.geometry.util import infer_geom_format
from ricco.geometry.util import is_geojson
from ricco.geometry.util import is_shapely
from ricco.geometry.util import is_wkb
from ricco.geometry.util import is_wkt

point_name = '点位A'
point_lng = 121.505563
point_lat = 31.31038
point_shapely = Point(point_lng, point_lat)
point_wkb = '0101000020E610000054C4E9245B605E401D554D10754F3F40'

polygon_name = '板块B'
p1 = Point(121.4952839926596653, 31.3133866150263032)
p2 = Point(121.5195342448080282, 31.3134999823890041)
p3 = Point(121.5116388138760612, 31.2944240039077783)
polygon_shapely = MultiPolygon([Polygon([p1, p2, p3, p1])])
polygon_wkb = '0106000020E6100000010000000103000000010000000400000028ADA1BBB25F5E40C88AEE1A3A503F4090A68F0C40615E4048A8EB8841503F40903DB9B0BE605E40F8F01B5F5F4B3F4028ADA1BBB25F5E40C88AEE1A3A503F40'
polygon_wkt = 'MULTIPOLYGON (((121.4952839926596653 31.3133866150263032, 121.5195342448080282 31.3134999823890041, 121.5116388138760612 31.2944240039077783, 121.4952839926596653 31.3133866150263032)))'

point_df = pd.DataFrame({
  'name': [point_name], 'lng': [point_lng], 'lat': [point_lat],
  'geometry_shapely': [point_shapely], 'geometry_wkb': [point_wkb],
})
point_df['geometry_shapely'] = point_df['geometry_shapely'].astype('geometry')

polygon_df = pd.DataFrame({
  '板块': [polygon_name], 'geometry_wkb': [polygon_wkb],
  'geometry_shapely': [polygon_shapely],
})
polygon_df['geometry_shapely'] = polygon_df['geometry_shapely'].astype(
    'geometry')

res_df = pd.DataFrame({
  'name': [point_name], 'lng': [point_lng], 'lat': [point_lat],
  'geometry_shapely': [point_shapely], 'geometry_wkb': [point_wkb],
  '板块': [polygon_name]
})
res_df['geometry_shapely'] = res_df['geometry_shapely'].astype('geometry')


def test_get_epsg():
  assert get_epsg('郑州') == 32649
  assert get_epsg('郑州市') == 32649
  assert get_epsg('上海') == 32651
  # test warning
  with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    city = '一个没有的市'
    assert get_epsg(city) == 32649
    assert len(w) == 1
    assert issubclass(w[-1].category, UserWarning)
    assert f'请补充"{city}"的epsg信息，默认返回经度113.0' in str(w[-1].message)


def test_mark_tags_v2():
  """测试空间连接打标签的方法"""

  # lnglat -- wkb
  df1 = pd.DataFrame(point_df[['name', 'lng', 'lat']])
  df2 = pd.DataFrame(polygon_df[[
    '板块', 'geometry_wkb']].rename(columns={'geometry_wkb': 'geometry'}))
  df3 = pd.DataFrame(res_df[['name', 'lng', 'lat', '板块']])
  assert_frame_equal(mark_tags_v2(df1, df2, '板块'), df3)

  # wkb -- wkb, with lnglat
  assert_frame_equal(
      mark_tags_v2(
          point_df[['name', 'lng', 'lat', 'geometry_wkb']].rename(
              columns={'geometry_wkb': 'geometry'}),
          polygon_df[['板块', 'geometry_wkb']].rename(
              columns={'geometry_wkb': 'geometry'}),
          c_tags=['板块'],
      ),
      res_df[['name', 'lng', 'lat', 'geometry_wkb', '板块']].rename(
          columns={'geometry_wkb': 'geometry'})
  )

  # wkb -- wkb, no lnglat
  assert_frame_equal(
      mark_tags_v2(
          point_df[['name', 'geometry_wkb']].rename(
              columns={'geometry_wkb': 'geometry'}),
          polygon_df[['板块', 'geometry_wkb']].rename(
              columns={'geometry_wkb': 'geometry'}),
          c_tags=['板块'],
      ),
      res_df[['name', 'geometry_wkb', '板块']].rename(
          columns={'geometry_wkb': 'geometry'})
  )

  # drop_geometry
  assert_frame_equal(
      mark_tags_v2(
          point_df[['name', 'lng', 'lat']],
          polygon_df[['板块', 'geometry_wkb']].rename(
              columns={'geometry_wkb': 'geometry'}),
          c_tags=['板块'],
          drop_geometry=True
      ),
      res_df[['name', 'lng', 'lat', '板块']]
  )
  # shapely -- shapely, no lnglat
  assert_frame_equal(
      mark_tags_v2(
          point_df[['name', 'geometry_shapely']].rename(
              columns={'geometry_shapely': 'geometry'}),
          polygon_df[['板块', 'geometry_shapely']].rename(
              columns={'geometry_shapely': 'geometry'}),
          c_tags=['板块'],
      ),
      res_df[['name', 'geometry_wkb', '板块']].rename(
          columns={'geometry_wkb': 'geometry'})
  )

  # shapely -- shapely, no lnglat, return shapely
  assert_frame_equal(
      mark_tags_v2(
          point_df[['name', 'geometry_shapely']].rename(
              columns={'geometry_shapely': 'geometry'}),
          polygon_df[['板块', 'geometry_shapely']].rename(
              columns={'geometry_shapely': 'geometry'}),
          c_tags=['板块'],
          geometry_format='shapely'
      ),
      res_df[['name', 'geometry_shapely', '板块']].rename(
          columns={'geometry_shapely': 'geometry'})
  )


def test_mark_tags_v22():
  """测试空间连接打标签的方法"""
  mapping = {
    'lng': 'lng2',
    'lat': 'lat2',
    'geometry_wkb': 'geometry_wkb2',
    'geometry_shapely': 'geometry_shapely2',
  }
  point = point_df.rename(columns=mapping)
  polygon = polygon_df.rename(columns=mapping)
  res = res_df.rename(columns=mapping)
  # lnglat -- wkb
  assert_frame_equal(
      mark_tags_v2(
          point[['name', 'lng2', 'lat2']],
          polygon[['板块', 'geometry_wkb2']].rename(
              columns={'geometry_wkb2': 'geometry2'}),
          c_tags=['板块'],
          c_lng='lng2',
          c_lat='lat2',
          c_geometry='geometry2',
          c_polygon_geometry='geometry2',
      ),
      res[['name', 'lng2', 'lat2', '板块']]
  )

  # wkb -- wkb, with lnglat
  assert_frame_equal(
      mark_tags_v2(
          point[['name', 'lng2', 'lat2', 'geometry_wkb2']].rename(
              columns={'geometry_wkb2': 'geometry2'}),
          polygon[['板块', 'geometry_wkb2']].rename(
              columns={'geometry_wkb2': 'geometry2'}),
          c_tags=['板块'],
          c_lng='lng2',
          c_lat='lat2',
          c_geometry='geometry2',
          c_polygon_geometry='geometry2',
      ),
      res[['name', 'lng2', 'lat2', 'geometry_wkb2', '板块']].rename(
          columns={'geometry_wkb2': 'geometry2'})
  )

  # wkb -- wkb, no lnglat
  assert_frame_equal(
      mark_tags_v2(
          point[['name', 'geometry_wkb2']].rename(
              columns={'geometry_wkb2': 'geometry2'}),
          polygon[['板块', 'geometry_wkb2']].rename(
              columns={'geometry_wkb2': 'geometry2'}),
          c_tags=['板块'],
          c_lng='lng2',
          c_lat='lat2',
          c_geometry='geometry2',
          c_polygon_geometry='geometry2',
      ),
      res[['name', 'geometry_wkb2', '板块']].rename(
          columns={'geometry_wkb2': 'geometry2'})
  )

  # drop_geometry
  assert_frame_equal(
      mark_tags_v2(
          point[['name', 'lng2', 'lat2']],
          polygon[['板块', 'geometry_wkb2']].rename(
              columns={'geometry_wkb2': 'geometry2'}),
          c_tags=['板块'],
          drop_geometry=True,
          c_lng='lng2',
          c_lat='lat2',
          c_geometry='geometry2',
          c_polygon_geometry='geometry2',
      ),
      res[['name', 'lng2', 'lat2', '板块']]
  )
  # shapely -- shapely, no lnglat
  assert_frame_equal(
      mark_tags_v2(
          point[['name', 'geometry_shapely2']].rename(
              columns={'geometry_shapely2': 'geometry2'}),
          polygon[['板块', 'geometry_shapely2']].rename(
              columns={'geometry_shapely2': 'geometry2'}),
          c_tags=['板块'],
          c_lng='lng2',
          c_lat='lat2',
          c_geometry='geometry2',
          c_polygon_geometry='geometry2',
      ),
      res[['name', 'geometry_wkb2', '板块']].rename(
          columns={'geometry_wkb2': 'geometry2'})
  )

  # shapely -- shapely, no lnglat, return shapely
  assert_frame_equal(
      mark_tags_v2(
          point[['name', 'geometry_shapely2']].rename(
              columns={'geometry_shapely2': 'geometry2'}),
          polygon[['板块', 'geometry_shapely2']].rename(
              columns={'geometry_shapely2': 'geometry2'}),
          c_tags=['板块'],
          geometry_format='shapely',
          c_lng='lng2',
          c_lat='lat2',
          c_geometry='geometry2',
          c_polygon_geometry='geometry2',
      ),
      res[['name', 'geometry_shapely2', '板块']].rename(
          columns={'geometry_shapely2': 'geometry2'})
  )


def test_is_xxx():
  assert is_wkt(None) is False
  assert is_wkb(None) is False
  assert is_shapely(None) is False
  assert is_geojson(None) is False

  assert is_wkt(None, na=True) is True
  assert is_wkb(None, na=True) is True
  assert is_shapely(None, na=True) is True
  assert is_geojson(None, na=True) is True

  assert is_wkt('aaa') is False
  assert is_wkb('aaa') is False
  assert is_shapely('aaa') is False
  assert is_geojson('aaa') is False

  assert is_wkt('Point(1 1)') is True
  assert is_wkb('0101000020E6100000000000000000F03F000000000000F03F') is True
  assert is_shapely(Point(1, 1)) is True
  assert is_geojson('{"type": "Point", "coordinates": [1.0, 1.0]}') is True


def test_infer_geom_format():
  assert infer_geom_format(None) == 'unknown'
  assert infer_geom_format(
      '0101000020E61000009A9999999999F13F9A9999999999F13F') == 'wkb'
  assert infer_geom_format(Point(1.1, 1.1)) == 'shapely'
  assert infer_geom_format('POINT (1.1 1.1)') == 'wkt'
  assert infer_geom_format(['POINT (1.1 1.1)']) == 'wkt'
  assert infer_geom_format(('POINT (1.1 1.1)',)) == 'wkt'
  assert infer_geom_format(pd.Series(['POINT (1.1 1.1)'])) == 'wkt'
