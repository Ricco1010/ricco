import logging
import time

# 64 位 id 的划分,通常机器位和数据位各为 5 位
WORKER_ID_BITS = 5  # 机器位
DATACENTER_ID_BITS = 5  # 数据位
SEQUENCE_BITS = 12  # 循环位

# 最大取值计算,计算机中负数表示为他的补码
MAX_WORKER_ID = -1 ^ (-1 << WORKER_ID_BITS)  # 2**5 -1 =31
MAX_DATACENTER_ID = -1 ^ (-1 << DATACENTER_ID_BITS)

# 移位偏移计算
WORKER_ID_SHIFT = SEQUENCE_BITS
DATACENTER_ID_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS
TIMESTAMP_LEFT_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS + DATACENTER_ID_BITS

# X序号循环掩码
SEQUENCE_MASK = -1 ^ (-1 << SEQUENCE_BITS)

# Twitter 元年时间戳
TWEPOCH = 1288834974657

logger = logging.getLogger('雪花算法')


class IdGenerator:
  """
  用于生成IDS.

  Args:
    datacenter_id:数据id
    worker_id:机器id
    sequence:序列码
  """

  def __init__(self, datacenter_id=1, worker_id=1, sequence=0):
    assert 0 <= worker_id <= MAX_WORKER_ID, f'worker_id 值越界，范围为0-{MAX_WORKER_ID}'
    assert 0 <= datacenter_id <= MAX_DATACENTER_ID, f'datacenter_id 值越界，范围为0-{MAX_DATACENTER_ID}'

    self.worker_id = worker_id
    self.datacenter_id = datacenter_id
    self.sequence = sequence
    self.last_timestamp = -1  # 上次计算的时间戳
    time.sleep(0.001)  # 避免多次实例化调取方法导致id重复

  @staticmethod
  def _gen_timestamp():
    """生成整数时间戳"""
    return int(time.time() * 1000)

  def _til_next_millis(self, last_timestamp):
    """等到下一毫秒"""
    timestamp = self._gen_timestamp()
    while timestamp <= last_timestamp:
      timestamp = self._gen_timestamp()
    return timestamp

  def get_id(self):
    """获取新的ID"""
    # 获取当前时间戳
    timestamp = self._gen_timestamp()

    # 时钟回拨的情况
    if timestamp < self.last_timestamp:
      logging.error(
          'clock is moving backwards. Rejecting requests util {}'.format(
              self.last_timestamp))
      raise Exception('无效的系统时钟')

    if timestamp == self.last_timestamp:
      # 同一毫秒的处理。
      self.sequence = (self.sequence + 1) & SEQUENCE_MASK
      if self.sequence == 0:
        timestamp = self._til_next_millis(self.last_timestamp)
    else:
      self.sequence = 0

    self.last_timestamp = timestamp

    return (
        ((timestamp - TWEPOCH) << TIMESTAMP_LEFT_SHIFT) |
        (self.datacenter_id << DATACENTER_ID_SHIFT) |
        (self.worker_id << WORKER_ID_SHIFT)
    ) | self.sequence

  def get_id_str(self):
    return str(int(self.get_id()))
