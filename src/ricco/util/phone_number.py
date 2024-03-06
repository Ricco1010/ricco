import random
import re
import warnings

from ..resource.patterns import Pattern
from ..resource.phone_number import service_providers


class PhoneNumber:
  def __init__(self, phone_number: str):
    self.phone_number = self.format_phone_number(phone_number)
    self.__3 = self.phone_number[:3]

  @property
  def value(self):
    return self.phone_number

  @staticmethod
  def is_valid(id_number) -> bool:
    """判断手机号是否有效"""
    string = str(id_number)
    if re.match(Pattern.phone_number, string):
      return True
    return False

  @staticmethod
  def not_valid(id_number) -> bool:
    """判断手机号是否无效"""
    return not PhoneNumber.is_valid(id_number)

  def format_phone_number(self, id_number) -> str:
    """对手机号进行校验并转为字符串格式"""
    if isinstance(id_number, (float, int)):
      id_number = str(int(id_number))
    if self.is_valid(id_number):
      return id_number
    else:
      raise ValueError('手机号格式错误')

  @property
  def service_providers(self):
    """手机运营商"""
    return service_providers.get(self.__3) or '未知'

  @property
  def home(self):
    # TODO(wangyukang): 补充手机号归属地
    warnings.warn('方法待补充')
    return

  @classmethod
  def random(cls):
    from ..resource.phone_number import service_providers
    _3 = random.choice(list(service_providers.keys()))
    _8 = random.randint(0, 99999999)
    _8 = str(_8).zfill(8)
    return f'{_3}{_8}'
