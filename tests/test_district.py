from ricco.util.district import District
from ricco.util.district import norm_city_name


def test_district():
  ds = District()
  assert ds.city(None) == None
  assert ds.city('') == None
  assert ds.city('单县') == '菏泽市'
  assert ds.city('杨浦区') == '上海市'
  assert ds.province(None) == None
  assert ds.province('') == None
  assert ds.province('滕州市') == '山东省'


def test_norm_city_name():
  assert norm_city_name('上海', full=True) == '上海市'
  assert norm_city_name('上海市', full=True) == '上海市'
  assert norm_city_name('上海市', full=False) == '上海'
  assert norm_city_name('上海', full=False) == '上海'
