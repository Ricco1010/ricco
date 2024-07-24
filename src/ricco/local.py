from functools import lru_cache

from .etl.extract import rdf

BASE_PATH = '/Users/ricco/common_data'


class Ricco:
  """通用数据"""

  @lru_cache
  def bd_region(self):
    return rdf(f'{BASE_PATH}/bd_region')

  def region(self, city='上海'):
    return rdf(f'{BASE_PATH}/行政边界/{city}边界_区县最新.csv')

  def street(self, city='上海'):
    return rdf(f'{BASE_PATH}/行政边界/{city}边界_街镇最新.csv')


Rc = Ricco()
