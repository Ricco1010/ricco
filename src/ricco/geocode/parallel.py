import time
import warnings
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from tqdm import tqdm

from ..util.decorator import timer
from ..util.district import ensure_city_name
from .request import func_call


def make_request(address, city, key, source, workers, qps):
  """发送单个请求的函数"""
  if qps <= 200:
    time.sleep(0.5 * workers / qps)
  try:
    js = func_call(source)(address, city, key)
    return str(js)
  except Exception as e:
    print(f"请求失败: {address}, {city}, 错误: {str(e)}")
    return


@timer()
def geocode_parallel(
    df: pd.DataFrame,
    c_address: str,
    city: (str, list),
    key: str,
    source: str,
    qps: int = 30,
    workers: int = 4
):
  """
  并行Geocode请求主函数

  Args:
    df: 要进行geocoding的Dataframe
    c_address: 地址列
    city: 城市或城市列，字符串-城市，列表-城市列的字段名
    key: geocoding服务提供商的key
    source: geocoding服务提供商，baidu/amap/baidu_poi/amap_poi
    qps: 并发数
    workers: Geocoding时使用的worker数量
  """
  df = df.copy()
  # 准备参数列表
  if isinstance(city, list):
    param_list = list(zip(df[c_address], df[city[0]]))
  elif isinstance(city, str):
    if not ensure_city_name(city):
      warnings.warn(f"无效的城市名称: {city}，请检查输入参数类型")
    param_list = list(zip(df[c_address], [city] * df.shape[0]))
  else:
    raise ValueError("city参数类型错误, 应为字符串或列表")

  with ThreadPoolExecutor(max_workers=workers) as executor:
    results = list(
        tqdm(
            executor.map(
                lambda param: make_request(
                    address=param[0], city=param[1],
                    key=key, source=source,
                    workers=workers, qps=qps,
                ),
                param_list,
            ),
            total=df.shape[0]
        )
    )
  assert len(results) == len(param_list) == df.shape[0]
  df['source'] = source
  df['rv'] = results
  return df
