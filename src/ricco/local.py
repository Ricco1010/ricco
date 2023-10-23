from .etl.extract import rdf

BASE_PATH = '/Users/ricco/common_data'


class Ricco:
  """通用数据"""

  def aoi(self, city='上海'):
    return rdf(f'{BASE_PATH}/aoi/{city}_全要素底图.csv')

  def region(self, city='上海'):
    return rdf(f'{BASE_PATH}/bd_region/{city}边界_区县最新.csv')

  def street(self, city='上海'):
    return rdf(f'{BASE_PATH}/bd_region/{city}边界_街镇最新.csv')

  def juwei(self, city='上海'):
    return rdf(f'{BASE_PATH}/aoi/{city}_居委边界.csv')

  def xiaoqu(self, city='上海'):
    df = rdf(f'{BASE_PATH}/aoi/{city}边界_AOI.csv')
    return df

  def building_geom(
      self,
      city: str,
      *,
      region: str = None,
      street: str = None,
      subfix: str = '百度',
      all_cols: bool = False,
  ):
    cols = ['oid', '城市', '区县', '街镇', 'geometry']
    df = rdf(f'{BASE_PATH}/aoi/{city}边界_建筑边界_{subfix}.parquet',
             columns=None if all_cols else cols)
    if street:
      return df[df['街镇'] == street]
    if region:
      return df[df['区县'] == region]
    return df


Rc = Ricco()
