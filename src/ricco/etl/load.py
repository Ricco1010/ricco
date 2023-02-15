import csv

import pandas as pd


def to_csv_by_line(filename: str, data: list):
  """
  逐行写入csv文件
  :param filename: 文件名
  :param data: 要写入的数据列表
  :return:
  """
  with open(filename, 'a') as f:
    csv_write = csv.writer(f, dialect='excel')
    csv_write.writerow(data)


def to_sheets(df_dict: dict, filename: str):
  """
  将多个dataframe保存到不同的sheet中

  Args:
      df_dict: 要保存的数据集，格式为：{sheet_name: DataFrame}
      filename: 要保存的文件名
  """
  with pd.ExcelWriter(filename) as writer:
    for sheet_name, data in df_dict.items():
      data.to_excel(writer, sheet_name)
