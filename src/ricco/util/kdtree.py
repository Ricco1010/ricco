from .decorator import timer


def filter_by_dist(ind, dist, r):
  """通过距离列表筛选出距离小于r的点的位置"""
  outer = []
  for i, ds in enumerate(dist):
    inner = []
    for j, d in enumerate(ds):
      if d <= r:
        inner.append(ind[i][j])
    outer.append(inner)
  return outer


def filter_by_limit(ls, n: int):
  """筛选列表中的列表的前limit个元素"""
  return [i[:n] for i in ls]


@timer()
def kdtree_query_radius(xy_tree, xy_query, r, limit: int = None, leaf_size=2):
  from sklearn.neighbors import KDTree
  tree = KDTree(xy_tree, leaf_size=leaf_size)
  ind, dist = tree.query_radius(xy_query, r=r,
                                return_distance=True,
                                sort_results=True)
  ind = [list(i) for i in ind]
  if limit:
    ind = filter_by_limit(ind, limit)
    dist = filter_by_limit(dist, limit)
  return ind, dist


@timer()
def kdtree_query(xy_tree, xy_query, limit: int = None, r=None, leaf_size=2):
  from sklearn.neighbors import KDTree
  tree = KDTree(xy_tree, leaf_size=leaf_size)
  dist, ind = tree.query(
      xy_query,
      k=limit if limit else 1,
      return_distance=True)
  ind = [list(i) for i in ind]
  dist = [list(i) for i in dist]
  if r:
    ind = filter_by_dist(ind, dist, r)
    dist = filter_by_dist(dist, dist, r)
  return ind, dist


def kdtree_nearest(xy_tree,
                   xy_query,
                   limit: int = None,
                   r: float = None,
                   leaf_size=2):
  if limit or not (r or limit):
    return kdtree_query(xy_tree, xy_query, limit, leaf_size)
  return kdtree_query_radius(xy_tree, xy_query, r, limit, leaf_size)
