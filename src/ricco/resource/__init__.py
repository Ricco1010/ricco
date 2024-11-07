"""资源目录"""
import os


def resource_path(filename):
  return os.path.join(__path__[0], filename)


P_BD_REGION = resource_path('bd_region.csv')
P_POSTCODE = resource_path('postcode.csv')
P_STOPWORDS = resource_path('stopwords.txt')

UTIL_CN_NUM = {
  '〇': '0',
  '零': '0',
  '一': '1',
  '二': '2',
  '两': '2',
  '三': '3',
  '四': '4',
  '五': '5',
  '六': '6',
  '七': '7',
  '八': '8',
  '九': '9',
}
