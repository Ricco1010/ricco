from .etl.extract import rdf


class Dirs:
  p_huamu_origin = '/Users/ricco/Project/collector_api_sdk/huamu'

  p_huamu_louyu = '/Users/ricco/Project/collector_api_sdk/huamu/花木街道-楼宇边界.csv'

  p_huamu_xiaoqu = '/Users/ricco/Project/collector_api_sdk/huamu/花木街道-小区边界.csv'

  p_huamu_shequ = '/Users/ricco/Project/collector_api_sdk/huamu/花木街道-社区边界.csv'

  p_huamu_juwei = '/Users/ricco/Project/collector_api_sdk/huamu/花木街道-居委边界.csv'

  def p_street(self, city):
    return f'/Users/ricco/common_data/{city}边界_街镇最新.csv'

  def p_region(self, city):
    return f'/Users/ricco/common_data/{city}边界_街镇最新.csv'


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


class Ricco(Datas):
  """常用文件"""
  pass
