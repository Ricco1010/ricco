import os

import pandas as pd

from .etl.extract import rdf


class Dirs:
  p_neurond = '/Users/ricco/neurond'

  p_huamu_origin = '/Users/ricco/Project/collector_api_sdk/huamu'

  p_huamu_louyu = '/Users/ricco/Project/collector_api_sdk/huamu/花木街道-楼宇边界.csv'

  p_huamu_xiaoqu = '/Users/ricco/Project/collector_api_sdk/huamu/花木街道-小区边界.csv'

  p_huamu_shequ = '/Users/ricco/Project/collector_api_sdk/huamu/花木街道-社区边界.csv'

  p_huamu_juwei = '/Users/ricco/Project/collector_api_sdk/huamu/花木街道-居委边界.csv'

  p_huamu_jumin = '/Users/ricco/Project/collector_api_sdk/huamu/花木市民-居民基本信息表.csv'

  p_huamu_juzhu = '/Users/ricco/Project/collector_api_sdk/huamu/花木市民-居民居住信息.csv'

  p_huamu_fangwu = '/Users/ricco/Project/collector_api_sdk/huamu/花木市民-房屋基本信息表.csv'

  def p_street(self, city):
    return f'/Users/ricco/common_data/bd_region/{city}边界_街镇最新.csv'

  def p_region(self, city):
    return f'/Users/ricco/common_data/bd_region/{city}边界_区县最新.csv'


class Datas(Dirs):
  def street(self, city='上海'):
    return rdf(self.p_street(city))

  def region(self, city='上海'):
    return rdf(self.p_region(city))

  def huamu_louyu(self):
    return rdf(self.p_huamu_louyu)

  def huamu_xiaoqu(self):
    return rdf(self.p_huamu_xiaoqu)

  def huamu_juwei(self):
    return rdf(self.p_huamu_juwei)

  def huamu_shequ(self):
    return rdf(self.p_huamu_shequ)

  def huamu_jumin(self):
    return rdf(self.p_huamu_jumin)

  def huamu_juzhu(self):
    return rdf(self.p_huamu_juzhu)

  def huamu_fangwu(self):
    return rdf(self.p_huamu_fangwu)


class AOI(Dirs):
  def building_geom(
      self,
      city: str,
      *,
      region: str = None,
      street: str = None,
      subfix: str = '百度',
      all_cols: bool = False,
  ):
    filename = f'{city}边界_建筑边界_{subfix}.parquet'
    fp = os.path.join('/Users/ricco/common_data/aoi/', filename)
    df = pd.read_parquet(fp)
    if not all_cols:
      df = df[['oid', '城市', '区县', '街镇', 'geometry']]
    if street:
      return df[df['街镇'] == street]
    if region:
      return df[df['区县'] == region]
    return df


class Ricco(Datas, AOI):
  """常用文件"""
  pass


Rc = Ricco()
