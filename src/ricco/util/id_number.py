import random
import re

import numpy as np
import pandas as pd

from ..resource.patterns import Pattern
from .random import random_date
from .util import physical_age


def get_check_code(id_number) -> str:
  mapping = {
    0: '1', 1: '0', 2: 'X', 3: '9', 4: '8',
    5: '7', 6: '6', 7: '5', 8: '4', 9: '3', 10: '2',
  }
  weight = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
  ils = [int(i) for i in id_number[:17]]
  return mapping.get(sum(np.multiply(weight, ils)) % 11)


class IDNumber:
  def __init__(self, id_number: str):
    self.id_number = self.format_id_number(id_number)
    self.__birthday = self.id_number[6:14]
    self.__gender = self.id_number[-2]

  @property
  def value(self):
    return self.id_number

  @staticmethod
  def is_valid(id_number, check_code=False) -> bool:
    """判断身份证号是否有效"""
    string = str(id_number)
    if re.match(Pattern.ID_number, string):
      if check_code:
        if get_check_code(string) != string[-1]:
          return False
      return True
    return False

  @staticmethod
  def not_valid(id_number, check_code=False) -> bool:
    """判断身份证号是否无效"""
    return not IDNumber.is_valid(id_number, check_code == check_code)

  def format_id_number(self, id_number) -> str:
    """对身份证号进行校验并转为字符串格式"""
    if isinstance(id_number, (float, int)):
      id_number = str(int(id_number))
    if self.is_valid(id_number):
      return id_number
    raise ValueError('身份证号格式错误')

  @property
  def check_code(self):
    return get_check_code(self.id_number)

  @property
  def birthdate(self):
    """出生日期"""
    return pd.to_datetime(self.__birthday, format='%Y%m%d')

  def birthday(self, format: str = '%Y-%m-%d') -> str:
    """出生日期"""
    return self.birthdate.strftime(format=format)

  @property
  def birth_int(self) -> int:
    """出生日期"""
    return int(self.birthdate.strftime(format='%Y%m%d'))

  @property
  def age(self) -> int:
    """年龄(周岁)"""
    return physical_age(self.birthdate)

  @property
  def gender(self) -> str:
    """性别"""
    return '女' if int(self.__gender) % 2 == 0 else '男'

  @property
  def sex(self) -> str:
    return self.gender

  @classmethod
  def random(cls):
    from ..resource.area_code import id_number_sbfix
    _6 = random.choice(list(id_number_sbfix.keys()))
    _birthday = random_date()
    _ord = random.randint(10, 99)
    _gender = random.randint(0, 9)
    id_number = f'{_6}{_birthday}{_ord}{_gender}'
    check_code = get_check_code(id_number)
    return id_number + check_code
