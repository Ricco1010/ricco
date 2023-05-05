import os

from tqdm import tqdm

from ..util.os import fn
from ..util.os import mkdir_2
from .extract import rdf


def split_csv(filename: str, n: int = 5, encoding: str = 'utf-8'):
  """将文件拆分为多个同名文件，放置在与文件同名文件夹下的不同Part_文件夹中"""
  dir_name = fn(os.path.basename(filename))
  abs_path = os.getcwd()
  df = rdf(filename)
  t = len(df)
  p = int(t / n)
  for i in tqdm(range(n)):
    low = i * p
    high = (i + 1) * p
    dir_name2 = 'Part_' + str(i)
    save_path = os.path.join(abs_path, dir_name, dir_name2)
    savefile = os.path.join(save_path, filename)
    mkdir_2(save_path)
    if i == n - 1:
      add = df.iloc[low:, :]
    else:
      add = df.iloc[low: high, :]
    add.to_csv(savefile, index=0, encoding=encoding)
