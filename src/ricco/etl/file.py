import os

from ..util.os import fn
from .extract import rdf
from .transformer import df_iter


def split2csvs(
    filename: str,
    *,
    chunksize: int = None,
    parts: int = None,
):
  """将文件拆分为多个文件，放置在与文件同名文件夹下"""
  if not any([chunksize, parts]):
    raise ValueError(f'chunksize 和 parts必须指定一个')
  full_path = os.path.abspath(filename)
  dir_name = fn(full_path)
  os.makedirs(dir_name, exist_ok=True)
  df = rdf(full_path)
  for i, df_part in enumerate(df_iter(df, chunksize=chunksize, parts=parts)):
    savefile = os.path.join(
        dir_name, f'part_{str(i + 1).zfill(len(str(parts)))}.csv')
    print(f'文件保存至：{savefile}, Rows：{df_part.shape[0]}')
    df_part.to_csv(savefile, index=0)
