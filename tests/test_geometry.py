import pandas as pd
from pandas.testing import assert_frame_equal
from shapely.geometry import Point

from ricco.geometry.df import mark_tags_v2
from ricco.geometry.util import get_epsg
from ricco.geometry.util import is_geojson
from ricco.geometry.util import is_shapely
from ricco.geometry.util import is_wkb
from ricco.geometry.util import is_wkt
from ricco.geometry.util import wkb_loads


def test_get_epsg():
  assert get_epsg('郑州') == 4547
  assert get_epsg('郑州市') == 4547
  assert get_epsg('一个没有的市') == 4549


def test_mark_tags_v2():
  """测试空间连接打标签的方法"""
  geom_polygon = '0106000020E6100000010000000103000000010000000400000028ADA1BBB25F5E40C88AEE1A3A503F4090A68F0C40615E4048A8EB8841503F40903DB9B0BE605E40F8F01B5F5F4B3F4028ADA1BBB25F5E40C88AEE1A3A503F40'
  geom_point = '0101000020E610000054C4E9245B605E401D554D10754F3F40'
  point = pd.DataFrame({
    'name': ['脉策科技'],
    'lng': [121.505563],
    'lat': [31.310380],
    'geometry_shapely': [Point(121.505563, 31.31038)],
    'geometry_wkb': [geom_point],
  })
  point['geometry_shapely'] = point['geometry_shapely'].astype('geometry')
  polygon = pd.DataFrame({
    '板块': ['五角场板块'],
    'geometry_wkb': [geom_polygon],
    'geometry_shapely': [wkb_loads(geom_polygon)],
  })
  polygon['geometry_shapely'] = polygon['geometry_shapely'].astype('geometry')

  res = pd.DataFrame({
    'name': ['脉策科技'],
    'lng': [121.505563],
    'lat': [31.310380],
    'geometry_shapely': [Point(121.505563, 31.31038)],
    'geometry_wkb': [geom_point],
    '板块': ['五角场板块']
  })
  res['geometry_shapely'] = res['geometry_shapely'].astype('geometry')

  # lnglat -- wkb
  assert_frame_equal(
      mark_tags_v2(
          point[['name', 'lng', 'lat']],
          polygon[['板块', 'geometry_wkb']].rename(
              columns={'geometry_wkb': 'geometry'}),
          col_list=['板块'],
      ),
      res[['name', 'lng', 'lat', 'geometry_wkb', '板块']].rename(
          columns={'geometry_wkb': 'geometry'})
  )

  # wkb -- wkb, with lnglat
  assert_frame_equal(
      mark_tags_v2(
          point[['name', 'lng', 'lat', 'geometry_wkb']].rename(
              columns={'geometry_wkb': 'geometry'}),
          polygon[['板块', 'geometry_wkb']].rename(
              columns={'geometry_wkb': 'geometry'}),
          col_list=['板块'],
      ),
      res[['name', 'lng', 'lat', 'geometry_wkb', '板块']].rename(
          columns={'geometry_wkb': 'geometry'})
  )

  # wkb -- wkb, no lnglat
  assert_frame_equal(
      mark_tags_v2(
          point[['name', 'geometry_wkb']].rename(
              columns={'geometry_wkb': 'geometry'}),
          polygon[['板块', 'geometry_wkb']].rename(
              columns={'geometry_wkb': 'geometry'}),
          col_list=['板块'],
      ),
      res[['name', 'geometry_wkb', '板块']].rename(
          columns={'geometry_wkb': 'geometry'})
  )

  # drop_geometry
  assert_frame_equal(
      mark_tags_v2(
          point[['name', 'lng', 'lat']],
          polygon[['板块', 'geometry_wkb']].rename(
              columns={'geometry_wkb': 'geometry'}),
          col_list=['板块'],
          drop_geometry=True
      ),
      res[['name', 'lng', 'lat', '板块']]
  )
  # shapely -- shapely, no lnglat
  assert_frame_equal(
      mark_tags_v2(
          point[['name', 'geometry_shapely']].rename(
              columns={'geometry_shapely': 'geometry'}),
          polygon[['板块', 'geometry_shapely']].rename(
              columns={'geometry_shapely': 'geometry'}),
          col_list=['板块'],
      ),
      res[['name', 'geometry_wkb', '板块']].rename(
          columns={'geometry_wkb': 'geometry'})
  )

  # shapely -- shapely, no lnglat, return shapely
  assert_frame_equal(
      mark_tags_v2(
          point[['name', 'geometry_shapely']].rename(
              columns={'geometry_shapely': 'geometry'}),
          polygon[['板块', 'geometry_shapely']].rename(
              columns={'geometry_shapely': 'geometry'}),
          col_list=['板块'],
          geometry_format='shapely'
      ),
      res[['name', 'geometry_shapely', '板块']].rename(
          columns={'geometry_shapely': 'geometry'})
  )


def test_mark_tags_v22():
  """测试空间连接打标签的方法"""
  geom_polygon = '0106000020E6100000010000000103000000010000000400000028ADA1BBB25F5E40C88AEE1A3A503F4090A68F0C40615E4048A8EB8841503F40903DB9B0BE605E40F8F01B5F5F4B3F4028ADA1BBB25F5E40C88AEE1A3A503F40'
  geom_point = '0101000020E610000054C4E9245B605E401D554D10754F3F40'
  point = pd.DataFrame({
    'name': ['脉策科技'],
    'lng2': [121.505563],
    'lat2': [31.310380],
    'geometry_shapely2': [Point(121.505563, 31.31038)],
    'geometry_wkb2': [geom_point],
  })
  point['geometry_shapely2'] = point['geometry_shapely2'].astype('geometry')
  polygon = pd.DataFrame({
    '板块': ['五角场板块'],
    'geometry_wkb2': [geom_polygon],
    'geometry_shapely2': [wkb_loads(geom_polygon)],
  })
  polygon['geometry_shapely2'] = polygon['geometry_shapely2'].astype(
      'geometry')

  res = pd.DataFrame({
    'name': ['脉策科技'],
    'lng2': [121.505563],
    'lat2': [31.310380],
    'geometry_shapely2': [Point(121.505563, 31.31038)],
    'geometry_wkb2': [geom_point],
    '板块': ['五角场板块']
  })
  res['geometry_shapely2'] = res['geometry_shapely2'].astype('geometry')

  # lnglat -- wkb
  assert_frame_equal(
      mark_tags_v2(
          point[['name', 'lng2', 'lat2']],
          polygon[['板块', 'geometry_wkb2']].rename(
              columns={'geometry_wkb2': 'geometry2'}),
          col_list=['板块'],
          point_lng='lng2',
          point_lat='lat2',
          point_geometry='geometry2',
          polygon_geometry='geometry2',
      ),
      res[['name', 'lng2', 'lat2', 'geometry_wkb2', '板块']].rename(
          columns={'geometry_wkb2': 'geometry2'})
  )

  # wkb -- wkb, with lnglat
  assert_frame_equal(
      mark_tags_v2(
          point[['name', 'lng2', 'lat2', 'geometry_wkb2']].rename(
              columns={'geometry_wkb2': 'geometry2'}),
          polygon[['板块', 'geometry_wkb2']].rename(
              columns={'geometry_wkb2': 'geometry2'}),
          col_list=['板块'],
          point_lng='lng2',
          point_lat='lat2',
          point_geometry='geometry2',
          polygon_geometry='geometry2',
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
          col_list=['板块'],
          point_lng='lng2',
          point_lat='lat2',
          point_geometry='geometry2',
          polygon_geometry='geometry2',
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
          col_list=['板块'],
          drop_geometry=True,
          point_lng='lng2',
          point_lat='lat2',
          point_geometry='geometry2',
          polygon_geometry='geometry2',
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
          col_list=['板块'],
          point_lng='lng2',
          point_lat='lat2',
          point_geometry='geometry2',
          polygon_geometry='geometry2',
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
          col_list=['板块'],
          geometry_format='shapely',
          point_lng='lng2',
          point_lat='lat2',
          point_geometry='geometry2',
          polygon_geometry='geometry2',
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
