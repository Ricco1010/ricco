import datetime

from ricco.util.id_number import get_check_code
from ricco.util.id_number import IDNumber

id_t = '110000200001010000'
id_f = '110000200001010001'


def test_get_check_code():
  assert get_check_code(id_t) == '0'
  assert get_check_code(id_f) == '0'


def test_IDNumber():
  assert IDNumber(id_t).check_code == '0'
  assert IDNumber(id_t).gender == '女'
  assert IDNumber(id_t).sex == '女'
  assert IDNumber(id_t).birthdate == datetime.datetime(2000, 1, 1)
  assert IDNumber(id_t).birth_int == 20000101
  assert IDNumber(id_t).birthday() == '2000-01-01'
  assert IDNumber.is_valid(id_t) == True
  assert IDNumber.is_valid(id_t, check_code=True) == True
  assert IDNumber.is_valid(id_f) == True
  assert IDNumber.is_valid(id_f, check_code=True) == False
