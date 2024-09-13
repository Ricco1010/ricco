import re
import warnings

from ..geometry.df import mark_tags_v2
from .strings import drop_repeat_string
from .util import union_str_v2


def make_building_address(
    df,
    *,
    c_hao,
    c_lu=None,
    c_nong=None,
    c_xiaoqu=None,
    c_dst: str = '楼宇地址',
):
  """
  根据【路弄号】或【小区地址和号】生成新版楼宇地址，格式为xx路xx弄xx号

  Args:
    df: dataframe
    c_hao: 号/楼栋号的列名
    c_lu: 路的列名
    c_nong: 弄的列名
    c_xiaoqu: 小区的列名，合适为"xx路xx弄[xx小区]"，用于提取路和弄
    c_dst: 生成楼宇地址的列名，默认为"楼宇地址"
  """
  for c in [c_hao, c_lu, c_xiaoqu]:
    if c and any(df[c].isna()):
      raise ValueError(f'{c}不可为空')
  if c_dst in df:
    warnings.warn(f'原数据中已存在{c_dst}列，已替换')
  if all([c_lu, c_nong]):
    df[c_dst] = df.apply(
        lambda r: union_str_v2(r[c_lu], r[c_nong], r[c_hao]), axis=1)
  elif c_xiaoqu:
    df[c_dst] = df.apply(
        lambda r: drop_repeat_string(
            union_str_v2(
                r[c_xiaoqu].split('[')[0], r[c_hao]
            )
        ),
        axis=1
    )
  else:
    raise KeyError('lu,nong和xiaoqu不能同时缺失')
  return df


def filter_dup_building(df,
                        xiaoqu,
                        c_building='楼宇地址',
                        c_xiaoqu='小区名称'):
  """
  通过小区边界和楼宇边界的空间关联，筛选同一小区的相同楼栋号
  Args:
    df: 楼宇边界
    xiaoqu: 小区边界
    c_building: 楼宇地址列名
    c_xiaoqu: 小区名称列名
  """
  if not xiaoqu[c_xiaoqu].is_unique:
    raise ValueError(f'{c_xiaoqu}存在重复值')

  df = mark_tags_v2(df, xiaoqu, c_tags=[c_xiaoqu])

  df = df[df[c_xiaoqu].notna() & df[c_building].notna()]

  return df[df.duplicated(subset=[c_xiaoqu, c_building])]


class BuildingAddress:
  def __init__(self, building: str):
    self.building = building

  @staticmethod
  def is_valid(building):
    if re.match('^.*路(\d+弄)?\d+-?\d*号楼?$', building):
      return True
    return False

  @property
  def road(self):
    """路"""
    if road_list := re.findall('^.+路', self.building):
      return road_list[0]

  @property
  def lane(self):
    """弄"""
    if lane_list := re.findall('路(.+弄)', self.building):
      return lane_list[0]

  @property
  def num(self):
    """号"""
    if num_list := re.findall('(?:.+路.+弄|.+路)(.+号楼?$)', self.building):
      return num_list[0]
    if num_list := re.findall('\d+号楼?', self.building):
      return num_list[0]

  @property
  def lu(self):
    """路"""
    return self.road

  @property
  def long(self):
    """弄"""
    return self.lane

  @property
  def nong(self):
    """弄"""
    return self.lane

  @property
  def hao(self):
    """号"""
    return self.num

  @property
  def std(self):
    return union_str_v2(self.road, self.lane, self.num)
