from ricco.util.district import District


def test_district():
  ds = District()
  assert ds.city(None) == None
  assert ds.city('') == None
  assert ds.city('单县') == '菏泽市'
  assert ds.city('杨浦区') == '上海市'
  assert ds.province(None) == None
  assert ds.province('') == None
  assert ds.province('滕州市') == '山东省'
