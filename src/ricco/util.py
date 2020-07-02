
def ensure_list(val):
  """将标量值和Collection类型都统一转换为LIST类型"""
  if val is None:
    return []
  if isinstance(val, list):
    return val
  if isinstance(val, (set, tuple)):
    return list(val)
  return [val]


def add(x, y):
  return x + y
