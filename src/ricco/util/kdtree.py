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
  """
  使用kdtree查询半径为r的点

  Args:
    xy_tree: 要构造数的点集
    xy_query: 查询的点集
    r: 查询半径
    limit: 数量限制
    leaf_size: kdtree叶子节点的大小
  """
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
  """
  使用kdtree查询最近的一个或多个点

  Args:
    xy_tree: 要构造数的点集
    xy_query: 查询的点集
    limit: 数量限制
    r: 半径限制
    leaf_size: kdtree叶子节点的大小
  """
  from sklearn.neighbors import KDTree
  tree = KDTree(xy_tree, leaf_size=leaf_size)
  dist, ind = tree.query(
      xy_query,
      k=limit or 1,
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
  """使用kdtree查询最近点"""
  if limit or not (r or limit):
    return kdtree_query(
        xy_tree=xy_tree,
        xy_query=xy_query,
        limit=limit,
        r=r,
        leaf_size=leaf_size)
  return kdtree_query_radius(
      xy_tree=xy_tree,
      xy_query=xy_query,
      r=r,
      limit=limit,
      leaf_size=leaf_size)
