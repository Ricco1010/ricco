import geopandas as gpd
from geopandas.testing import assert_geodataframe_equal
from shapely.geometry import MultiPolygon
from shapely.geometry import Polygon

from ricco.geometry.topology_check import fix_overlap
from ricco.geometry.topology_check import fix_self_intersection


def assert_geopandas(res: gpd.GeoDataFrame, test: gpd.GeoDataFrame):
  diff1 = res.overlay(test, how='difference')
  diff2 = test.overlay(res, how='difference')
  assert (diff1.empty or all(diff1['geometry'].area < 1e-5))
  assert (diff2.empty or all(diff2['geometry'].area < 1e-5))
  assert_geodataframe_equal(res[res['geometry'].is_empty],
                            test[test['geometry'].is_empty],
                            check_crs=False)


def test_fix_overlap():
  polygon1 = Polygon([(0, 0), (0, 4), (4, 4), (4, 0)])
  polygon2 = Polygon([(3, 0), (3, 4), (7, 4), (7, 0)])
  polygon3 = Polygon([(2, 2), (2, 3), (5, 3), (5, 2)])
  polygon4 = Polygon([(1, 1), (1, 3), (3, 3), (3, 1)])
  input1 = gpd.GeoDataFrame({'name': [0, 1],
                             'geometry': [MultiPolygon([polygon1, polygon2]),
                                          MultiPolygon([polygon3, polygon4])]},
                            geometry='geometry')
  res1 = fix_overlap(input1, fill_intersects=True, keep_contains=False)
  test1 = gpd.GeoDataFrame({
    'name': [0, 1],
    'geometry': [MultiPolygon([
        polygon1.difference(polygon2.buffer(1e-7)),
        polygon2
      ]),
      Polygon()]
  })
  assert_geopandas(res1, test1)

  res2 = fix_overlap(input1, fill_intersects=True, keep_contains=True)

  test2 = gpd.GeoDataFrame({
    'name': [0, 1],
    'geometry': [MultiPolygon([
      (polygon1.difference(polygon3.buffer(1e-7))
       .difference(polygon4.buffer(1e-7))
       .difference(polygon2.buffer(1e-7))),
      polygon2.difference(polygon3.buffer(1e-7))
    ]),
      MultiPolygon([
        polygon3.difference(polygon4.buffer(1e-7)),
        polygon4
      ]),
    ]
  })
  assert_geopandas(res2, test2)

  res3 = fix_overlap(input1, fill_intersects=False)

  test3 = gpd.GeoDataFrame({
    'name': [0, 1],
    'geometry': [MultiPolygon([
      (polygon1.difference(polygon3.buffer(1e-7))
       .difference(polygon4.buffer(1e-7))
       .difference(polygon2.buffer(1e-7))),
      (polygon2.difference(polygon3.buffer(1e-7))
       .difference(polygon4.buffer(1e-7)))
    ]),
      Polygon(),
    ]
  })
  assert_geopandas(res3, test3)

  polygon5 = Polygon([(1, 1), (1, 2), (2, 2), (2, 1)])
  input2 = gpd.GeoDataFrame({
    'name': [0, 1, 2],
    'geometry': [
      polygon1,
      polygon5,
      polygon4,
    ]
  })
  res4 = fix_overlap(input2, fill_intersects=True, keep_contains=True)
  test4 = gpd.GeoDataFrame({
    'name': [0, 1, 2],
    'geometry': [polygon1.difference(polygon4),
                 polygon5,
                 polygon4.difference(polygon5)]
  })
  assert_geopandas(res4, test4)


def test_fix_self_intersection():
  polygon1 = Polygon([(0, 0), (0, 4), (3, 4), (3, 3), (4, 3),
                      (4, 0), (4, 4), (3, 4), (3, 3), (4, 3),
                      (4, 0)])
  res1 = fix_self_intersection(polygon1)
  test1 = Polygon([(0, 0), (0, 4),  (4, 4), (4, 0)])
  assert res1.equals(test1)

  polygon2 = Polygon([(0, 0), (0, 4), (3, 4), (3, 3), (4, 3),
                      (4, 0), (4, 4), (3, 4), (3, 3), (4, 3),
                      (4, 0)], [[(1, 1), (1, 2), (2, 2), (2, 1)]])
  res2 = fix_self_intersection(polygon2)
  test2 = Polygon([(0, 0), (0, 4), (4, 4), (4, 0)],
                  [[(1, 1), (1, 2), (2, 2), (2, 1)]])
  assert res2.equals(test2)

  polygon3 = Polygon([(0, 0), (0, 2), (2, 0), (2, 2)])
  res3 = fix_self_intersection(polygon3)
  test3 = MultiPolygon([Polygon([(0, 0), (0, 2), (1, 1)]),
                        Polygon([(1, 1), (2, 2), (2, 0)])])
  assert res3.equals(test3)
