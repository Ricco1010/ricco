import datetime
import random

import numpy as np
import pandas as pd


def random_name():
  """随机生成中文名字，仅生成2或3字名字"""
  from ..resource.names import FirstName
  from ..resource.names import LastName
  c = [random.choice(FirstName)]
  for i in range(random.randint(1, 2)):
    c.append(random.choice(LastName))
  return ''.join(c)


def random_date():
  """获取随机日期"""
  now = datetime.datetime.now()
  tsp = int(datetime.datetime.timestamp(now))
  tsp = random.randrange(-946800000, tsp)
  return datetime.datetime.fromtimestamp(tsp).strftime("%Y%m%d")


def random_room_number(unit=False):
  """生成随机的房间号"""
  floor = random.randint(1, 17)
  room = random.randint(1, 4)
  room = str(room).zfill(2)
  if unit:
    _u = random.randint(1, 6)
    _unit = f'{_u}单元'
    return f'{_unit}{floor}{room}'
  return f'{floor}{room}'


def random_by_prob(mapping: dict):
  """根据概率生成随机值"""
  return np.random.choice(
      list(mapping.keys()),
      p=np.array(list(mapping.values())).ravel()
  )


def ramdom_lnglat(
    df: pd.DataFrame,
    lng_range: (tuple, list) = (72, 138),
    lat_range: (tuple, list) = (0, 56),
):
  """
  随机生成经纬度

  Args:
    df: 输入的dataframe
    lng_range: 城市的经度范围
    lat_range: 城市的纬度范围
  """
  length = df.shape[0]
  df['lng'] = np.random.uniform(*lng_range, length)
  df['lat'] = np.random.uniform(*lat_range, length)
  return df
