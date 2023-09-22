import pandas as pd

from ..util.assertion import assert_not_null
from ..util.decorator import singleton
from ..util.util import is_empty


@singleton
def get_graph_dict(graph_df: (pd.DataFrame, dict),
                   c_key='id',
                   c_level_type='level_type',
                   c_parent_key='parent_id',
                   c_parent_type='parent_type'
                   ):
  graph_df = graph_df[[c_key, c_level_type, c_parent_key]]
  df_temp = graph_df[[c_key, c_level_type]]
  df_temp.columns = [c_parent_key, c_parent_type]
  graph_df = graph_df.merge(df_temp)
  # 构造查询字典
  return graph_df.set_index(c_key).to_dict()


def query_from_graph(key,
                     graph_df: (pd.DataFrame, dict),
                     c_key='id',
                     c_level_type='level_type',
                     c_parent_key='parent_id',
                     max_depth=10,
                     ) -> dict:
  """
  从图数据中查询全部父级节点
  Args:
    key: 要查询的节点
    graph_df: 要查询的数据集
    c_key: 子节点关键列的字段名
    c_level_type: 等级类型字段名
    c_parent_key: 父节点字段名
    max_depth: 最大深度
  """
  assert isinstance(graph_df, pd.DataFrame)
  assert graph_df[c_key].is_unique
  assert_not_null(graph_df, c_level_type), f'{c_level_type}不能为空'
  assert graph_df[graph_df[c_key] == graph_df[c_parent_key]].empty, '父子不能相同'
  # 构造查询字典
  c_parent_type = 'parent_type'
  graph_dict = get_graph_dict(graph_df=graph_df, c_key=c_key,
                              c_level_type=c_level_type,
                              c_parent_key=c_parent_key,
                              c_parent_type=c_parent_type)
  level_type = graph_dict[c_level_type].get(key)
  if not level_type:
    return {}
  res = {level_type: key}
  # 循环查询上级关系
  depth = 0
  while depth < max_depth:
    parent_key = graph_dict[c_parent_key].get(key)
    parent_type = graph_dict[c_parent_type].get(key)
    if is_empty(parent_key):
      break
    res[parent_type] = parent_key
    key = parent_key
    depth += 1
  return res
