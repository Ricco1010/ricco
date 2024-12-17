from ricco.util.district import District
from ricco.util.district import get_city_and_region
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


def test_extract_city():
  s = '上海市杨浦区政立路111号'
  assert get_city_and_region(s) == ('上海市', '杨浦区', ['上海市'], ['杨浦区'])

  s = '浙江省杭州市滨江区西兴街道泰安路199号'
  assert get_city_and_region(s) == ('杭州市', '滨江区', ['杭州市'], ['滨江区'])

  s = '云南省红河哈尼族彝族自治州个旧市大屯镇团山村万城米兰春天25幢2号'
  assert get_city_and_region(s) == (
    '红河哈尼族彝族自治州', '个旧市', ['红河哈尼族彝族自治州'], ['个旧市']
  )

  s = '内蒙古乌兰察布市察哈尔右翼前旗平地泉北方汽车城B厅35号'
  assert get_city_and_region(s) == (
    '乌兰察布市', '察哈尔右翼前旗', ['乌兰察布市'], ['察哈尔右翼前旗']
  )

  s = '甘肃省武威市天祝藏族自治县东大滩乡圈湾村'
  assert get_city_and_region(s) == (
    '武威市', '天祝藏族自治县', ['武威市'], ['天祝藏族自治县']
  )

  s = '内蒙古自治区锡林郭勒盟锡林浩特市污水处理厂附近工业园区17号'
  assert get_city_and_region(s) == (
    '锡林郭勒盟', '锡林浩特市', ['锡林郭勒盟'], ['锡林浩特市']
  )

  s = '河北省石家庄市桥西区新石中路168号15栋2单元402室'
  assert get_city_and_region(s) == (
    '石家庄市', '桥西区', ['石家庄市'], ['桥西区']
  )
