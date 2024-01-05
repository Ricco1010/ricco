import warnings

import pandas as pd

from ..base import is_empty


def get_graph_dict(
    graph_df: pd.DataFrame,
    c_key='id',
    c_level_type='level_type',
    c_parent_key='parent_id',
    c_parent_type='parent_type'
) -> dict:
  """
  将图结构的Dataframe转为字典格式，提高查询效率

  Args:
    graph_df: 图结构的数据
    c_key: 索引列
    c_level_type: 层级分类列
    c_parent_key: 对应的父级索引列
    c_parent_type: 对应的父级类型列
  """
  graph_df = graph_df[[c_key, c_level_type, c_parent_key]]
  df_temp = graph_df[[c_key, c_level_type]]
  df_temp.columns = [c_parent_key, c_parent_type]
  graph_df = graph_df.merge(df_temp)
  # 构造查询字典
  return graph_df.set_index(c_key).to_dict()


def query_from_graph(
    key,
    graph_data: (pd.DataFrame, dict),
    c_key='id',
    c_level_type='level_type',
    c_parent_key='parent_id',
    max_depth=10,
) -> dict:
  """
  从图数据中查询全部当前节点的全部父级节点

  Args:
    key: 要查询的节点
    graph_data: 要查询的数据集
    c_key: 子节点关键列的字段名
    c_level_type: 等级类型字段名
    c_parent_key: 父节点字段名
    max_depth: 最大深度
  """

  # 构造查询字典
  c_parent_type = 'parent_type'
  if isinstance(graph_data, pd.DataFrame):
    warnings.warn(
        'graph_data 是一个 DataFrame, '
        '请使用 ricco.etl.graph.get_graph_dict 函数构造查询字典后传入，以提高查询效率')
    graph_dict = get_graph_dict(
        graph_df=graph_data, c_key=c_key, c_level_type=c_level_type,
        c_parent_key=c_parent_key, c_parent_type=c_parent_type)
  elif isinstance(graph_data, dict):
    graph_dict = graph_data
  else:
    raise TypeError('graph_data 类型错误，请传入 DataFrame 或 dict')
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
