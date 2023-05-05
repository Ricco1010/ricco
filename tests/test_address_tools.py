import numpy as np

from ricco.util.address_tools import is_std_hao
from ricco.util.address_tools import main
from ricco.util.address_tools import pre_process


def test_is_std_hao():
  assert is_std_hao('255号') is True
  assert is_std_hao('255号、256号') is True
  assert is_std_hao('258号、256号、256号') is True
  assert is_std_hao('255') is False
  assert is_std_hao('258、256号') is False
  assert is_std_hao('258号，256号') is False


def test_pre_process():
  assert pre_process(None) is None
  assert pre_process(np.nan) is None
  assert pre_process('255-1') == '255-1'
  assert pre_process('255—1') == '255-1'
  assert pre_process('255－1') == '255-1'
  assert pre_process('255~1') == '255-1'
  assert pre_process('255～1') == '255-1'
  assert pre_process('255～1?') == '255-1'
  assert pre_process('255～1？') == '255-1'
  assert pre_process('255～1 甲') == '255-1甲'
  assert pre_process('255乙号') == '255号乙'


def test_main():
  assert main('上海市普陀区甘泉路街道黄陵路255号') == {
    '省': None,
    '市': '上海市',
    '区': '普陀区',
    '街道': '甘泉路街道',
    '居委': None,
    '路': '黄陵路',
    '弄': None,
    '号': '255号',
    'subfix': None,
    'extra': '255号',
    'format': '黄陵路255号',
  }
  assert main('黄陵路255号-2') == {
    '省': None, '市': None, '区': None, '街道': None, '居委': None,
    '路': '黄陵路',
    '弄': None,
    '号': '255号',
    'subfix': '2',
    'extra': '255号-2',
    'format': '黄陵路255号-2',
  }
  assert main('黄陵路255') == {
    '省': None, '市': None, '区': None, '街道': None, '居委': None,
    '路': '黄陵路',
    '弄': None,
    '号': '255号',
    'subfix': None,
    'extra': '255',
    'format': '黄陵路255号',
  }
  assert main('宜君路51—1号') == {
    '省': None, '市': None, '区': None, '街道': None, '居委': None,
    '路': '宜君路',
    '弄': None,
    '号': '51号',
    'subfix': '1',
    'extra': '51-1号',
    'format': '宜君路51号-1',
  }
  assert main('宜君路51－1号') == {
    '省': None, '市': None, '区': None, '街道': None, '居委': None,
    '路': '宜君路',
    '弄': None,
    '号': '51号',
    'subfix': '1',
    'extra': '51-1号',
    'format': '宜君路51号-1',
  }
  assert main('宜君路51-1号') == {
    '省': None, '市': None, '区': None, '街道': None, '居委': None,
    '路': '宜君路',
    '弄': None,
    '号': '51号',
    'subfix': '1',
    'extra': '51-1号',
    'format': '宜君路51号-1',
  }
  assert main('宜川路351弄24号') == {
    '省': None, '市': None, '区': None, '街道': None, '居委': None,
    '路': '宜川路',
    '弄': '351弄',
    '号': '24号',
    'subfix': None,
    'extra': '24号',
    'format': '宜川路351弄24号',
  }
  assert main('宜川路351弄24号-3') == {
    '省': None, '市': None, '区': None, '街道': None, '居委': None,
    '路': '宜川路',
    '弄': '351弄',
    '号': '24号',
    'subfix': '3',
    'extra': '24号-3',
    'format': '宜川路351弄24号-3',
  }
  assert main('延长西路56号乙') == {
    '省': None, '市': None, '区': None, '街道': None, '居委': None,
    '路': '延长西路',
    '弄': None,
    '号': '56号',
    'subfix': '乙',
    'extra': '56号乙',
    'format': '延长西路56号-乙',
  }
  assert main('延长西路56甲号') == {
    '省': None, '市': None, '区': None, '街道': None, '居委': None,
    '路': '延长西路',
    '弄': None,
    '号': '56号',
    'subfix': '甲',
    'extra': '56号甲',
    'format': '延长西路56号-甲',
  }
  assert main('新村路31，33号') == {
    '省': None, '市': None, '区': None, '街道': None, '居委': None,
    '路': '新村路',
    '弄': None,
    '号': '31号、33号',
    'subfix': None,
    'extra': '31，33号',
    'format': '新村路31号、33号',
  }
