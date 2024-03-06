import re

import pandas as pd

from .strings import drop_repeat_string
from .util import relstrip

RES_PRE = {
  '省': None,
  '市': None,
  '区': None,
  '街道': None,
  '居委': None,
  '路': None,
  '弄': None,
  '号': None,
  'subfix': None,
  'extra': None,
  'format': None,
}


def drop_repeat_hao(string: str):
  """将重复的xx号中间的部分全部删掉"""
  ls = re.findall(r'[0-9]+号', string)
  if len(ls) >= 2:
    _df = pd.DataFrame({'号': ls})
    _df = pd.DataFrame(_df['号'].value_counts()).reset_index(names='name')
    if _df['号'][0] >= 2:
      sep = _df['name'][0]
      _parts = string.split(sep)
      return sep.join([_parts[0], _parts[-1]])
  return string


def split_by_keyword(string):
  """按照关键词对地址进行初步拆分"""
  seps = {
    '省': ['省', '自治区'],
    '市': ['市'],
    '区': ['区', '县'],
    '街道': ['镇', '街道'],
    '居委': ['居委'],
    '路': ['路', '大道'],
    '弄': ['弄'],
  }
  if '集市' in string:
    string = string.replace('集市', 'vvjishivv')
  res = RES_PRE.copy()
  for key, kwds in seps.items():
    res[key] = None
    for kwd in kwds:
      s_list = string.split(kwd, 1)
      if len(s_list) == 2:
        res[key] = s_list[0] + key
        string = s_list[1]
        break
  res['extra'] = None if string == '' else string
  return res


def clean_after_split(string: str):
  """清洗提取后的值"""
  if not isinstance(string, str):
    return string
  # 删除分隔符
  for pat in ['/', '-', '—', '－']:
    string = string.strip(pat)
  string = string.replace('vvjishivv', '集市')
  return None if string == '' else string


def process_by_dict(input_dict: dict):
  """批量处理提取后的值"""
  for k, v in input_dict.items():
    input_dict[k] = clean_after_split(v)
  return input_dict


def is_std_hao(string):
  """
  检查号相关的字符串是否为标准格式，仅检查是否为"xx号、xx号"的形式，不检查重复值和顺序
  """
  ls = string.split('、')
  return all([re.match('^[0-9]+号$', i) for i in ls])


def hao_format(string):
  """对"号"部分进行标准化，主要操作为去重和排序"""
  ls = list(set(string.split('、')))
  ls.sort()
  return '、'.join(ls)


def extract_seps(string):
  _ = []
  ls = re.split('[、|，]', string)
  for i in ls:
    if re.match('^[0-9]+$', i):
      _.append(i + '号')
    if re.match('^[0-9]+号$', i):
      _.append(i)
  _ = list(set(_))
  _.sort()
  return '、'.join(_)


def extra_process(string):
  """提取xx号和后缀，xx号之后的都认为是后缀"""
  res = {
    '号': None,
    'subfix': None,
  }

  if pd.isna(string) or string == '':
    return

  # 类似标准格式的，标准化后直接返回
  if is_std_hao(string):
    res['号'] = hao_format(string)
    return res

  # 路名之后为纯数字的认为是xx号
  if pre_str := re.findall('^[0-9]+$', string):
    res['号'] = pre_str[0] + '号'
    return res

  # 范围号提取，如221-223是221号、222号、223号
  if pre_str := re.findall('^[0-9]+号?[-—－一][0-9]+号?', string):
    pre_str = pre_str[0]
    ls = [int(i) for i in re.findall('[0-9]+', pre_str)]
    sub_str = relstrip(string, pre_str).lstrip('号')
    res['subfix'] = None if sub_str == '' else sub_str
    if ls[0] > ls[1]:
      res['号'] = str(ls[0]) + '号'
      res['subfix'] = str(ls[1]) + sub_str
    # elif any([i in string for i in ['奇', '偶', '单', '双']]):
    else:
      res['号'] = '、'.join([f'{i}号' for i in range(ls[0], ls[1] + 2, 2)])
    # 认为同一个地址为xx号-xx号的"号"要么是奇数要么是偶数
    # else:
    #   res['号'] = '、'.join([f'{i}号' for i in range(ls[0], ls[1] + 1, 1)])
    return res

  # 枚举号提取，如"221号，222号"或"221、222号"，提取结果为："221号、222号"
  if pre_str := re.findall('^[0-9]+号?(?:[、，][0-9]+号?)*', string):
    pre_str = pre_str[0]
    res['号'] = extract_seps(pre_str)
    res['subfix'] = clean_after_split(relstrip(string, pre_str))
    return res

  # 直接提取xx号，仅提取第一个
  if pre_str := re.findall(r'^[0-9]+号', string):
    pre_str = pre_str[0]
    sub_str = relstrip(string, pre_str).lstrip('号')
    res['号'] = pre_str
    res['subfix'] = clean_after_split(sub_str)
    return res

  if not res['号']:
    res['subfix'] = string

  return res


def extract_extra(res):
  if not res['extra']:
    return res
  res['extra'] = drop_repeat_hao(res['extra'])
  _ = extra_process(res['extra'])
  res['号'] = _['号']
  res['subfix'] = _['subfix']
  return res


def pre_process(string: str):
  """对字符串进行预处理，统一部分字符，删除空格及特殊字符"""
  if pd.isna(string):
    return

  string = str(string)
  for s in ['—', '－', '~', '～']:
    string = string.replace(s, '-')
  for s in ['?', '？']:
    string = string.replace(s, '')
  string = ''.join(string.split())

  # 将"xx甲号"改为"xx号甲"
  if ls := re.findall('[0-9]+[甲乙丙丁戊己庚辛壬癸]号', string):
    for str_o in ls:
      s1 = re.findall('^[0-9]+', str_o)[0]
      s2 = re.findall('[甲乙丙丁戊己庚辛壬癸]', str_o)[0]
      str_d = f'{s1}号{s2}'
      string = string.replace(str_o, str_d)
  if string == '':
    return
  return string


def formatted(res):
  """拼接为标准的地址"""
  res['format'] = (
      (res['路'] or '') +
      (res['弄'] or '') +
      (res['号'] or '') +
      ('-' if res['subfix'] and any(
          [res['路'], res['弄'], res['号']]
      ) else '') +
      (res['subfix'] or '')
  )
  return res


def main(string):
  string = pre_process(string)

  if pd.isna(string):
    return RES_PRE

  string = drop_repeat_string(string)
  # 初步提取
  res = split_by_keyword(string)
  # 提取结果简单清洗
  res = process_by_dict(res)
  # 对extra进行再次提取
  res = extract_extra(res)
  # 生成标准列
  res = formatted(res)
  return res
