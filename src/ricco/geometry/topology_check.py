def fix_polygon_topology(
    gdf, geo_col='geometry', fill_intersects=False, keep_contains=False  # noqa
):
  raise Exception(
      '`fix_polygon_topology`已经停用，'
      '请使用`ricco.geometry.topology.fix_topology`代替。'
  )
