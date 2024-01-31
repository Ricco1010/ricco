import geopandas as gpd
from geopandas.testing import assert_geodataframe_equal
from shapely.geometry import Polygon

from ricco.geometry.topology import fix_topology


def assert_geopandas(res: gpd.GeoDataFrame, test: gpd.GeoDataFrame):
  diff1 = res.overlay(test, how='difference', keep_geom_type=False)
  diff2 = test.overlay(res, how='difference', keep_geom_type=False)
  assert (diff1.empty or all(diff1['geometry'].area < 1e-5))
  assert (diff2.empty or all(diff2['geometry'].area < 1e-5))
  assert_geodataframe_equal(res[res['geometry'].is_empty],
                            test[test['geometry'].is_empty],
                            check_crs=False)


def test_fix_overlap():
  polygon1 = Polygon([(0, 0), (0, 4), (4, 4), (4, 0)])
  polygon2 = Polygon([(3, 0), (3, 4), (7, 4), (7, 0)])
  polygon4 = Polygon([(1, 1), (1, 3), (3, 3), (3, 1)])
  input1 = gpd.GeoDataFrame({'name': [0, 1],
                             'geometry': [polygon4, polygon1]},
                            geometry='geometry')
  res1 = fix_topology(input1, fill_intersects=True, keep_contains=False)
  res1.crs = None
  test1 = gpd.GeoDataFrame({'name': [0, 1],
                            'geometry': [
                              Polygon(),
                              polygon1
                            ]})
  assert_geopandas(res1, test1)

  input2 = gpd.GeoDataFrame({'name': [0, 1],
                             'geometry': [polygon4, polygon1]},
                            geometry='geometry')
  res2 = fix_topology(input2, fill_intersects=True, keep_contains=True)
  res2.crs = None

  test2 = gpd.GeoDataFrame({'name': [0, 1],
                            'geometry': [
                              polygon4,
                              polygon1.difference(polygon4.buffer(1e-7))
                            ]})
  assert_geopandas(res2, test2)

  input3 = gpd.GeoDataFrame({'name': [0, 1],
                             'geometry': [polygon2, polygon1]},
                            geometry='geometry')

  res3 = fix_topology(input3, fill_intersects=False)
  res3.crs = None

  test3 = gpd.GeoDataFrame({'name': [0, 1],
                            'geometry': [
                              polygon2.difference(polygon1.buffer(1e-7)),
                              polygon1.difference(polygon2.buffer(1e-7)),
                            ]})
  assert_geopandas(res3, test3)

  polygon5 = Polygon([(1, 1), (1, 2), (2, 2), (2, 1)])
  input4 = gpd.GeoDataFrame({
    'name': [0, 1, 2],
    'geometry': [
      polygon1,
      polygon5,
      polygon4,
    ]
  })
  res4 = fix_topology(input4, fill_intersects=True, keep_contains=True)
  res4.crs = None
  test4 = gpd.GeoDataFrame({'name': [0, 1, 2],
                            'geometry': [polygon1.difference(polygon4),
                                         polygon5,
                                         polygon4.difference(polygon5)]})
  assert_geopandas(res4, test4)
