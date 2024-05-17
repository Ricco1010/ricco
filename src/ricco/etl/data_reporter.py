import pandas as pd

from ..base import ensure_list
from ..util.decorator import print_doc
from ..util.docx import Docx
from .extract import rdf
from .stat import describe_auto
from .stat import suspect_series_type


class DataReporter(Docx):
  """
  数据检测并生成描述性统计报告，方便排查数据问题

  Args:
    data: 待检测的数据，文件路径或Dataframe
    only: 要检测的列
    exclude: 要排除的列，如果only有值，则以only为准
  """

  def __init__(
      self, data: (str, pd.DataFrame),
      only: list = None,
      exclude: list = None):
    self.set_default_style()
    self.doc.add_heading('数据检测报告', 0)
    if isinstance(data, pd.DataFrame):
      self.df = data
    else:
      self.add_intense_quote(f'Data：{data}')
      self.df = rdf(data, info=True)

    columns = list(self.df.columns)
    if not only:
      only = columns
    elif exclude:
      only = [c for c in columns if c not in exclude]

    self.only = ensure_list(only)
    self.df = self.df[only]

  @print_doc
  def preprocess(self):
    """数据预处理"""
    for c in self.only:
      if self.df[c].dtype not in (float, int, 'datetime64[ns]'):
        try:
          self.df[c] = pd.to_datetime(self.df[c])
        except Exception:
          pass

  @print_doc
  def basic(self):
    """基础信息描述"""
    self.add_normal_p(f'检测时间：{self.create_time}')
    # 列名
    self.add_title_1('列名')
    self.add_normal_p('，'.join(self.df.columns))
    # 文件size
    self.add_title_1('文件尺寸')
    self.add_normal_p(f'行：{self.df.shape[0]}，列：{self.df.shape[1]}')

    # 列类型
    self.add_title_1('字段名称及类型')
    col_types = pd.DataFrame(
        self.df.dtypes,
        columns=['类型']
    ).reset_index().rename(
        columns={'index': '列名'})
    self.add_table_from_df(col_types)

  @print_doc
  def col_by_col(self):
    """逐列检测"""
    self.add_title_1('字段检测明细')
    for col in self.df.columns:
      self.add_title_3(f'字段：{col}')

      # 空列直接跳过，不进行后续的检查
      if self.df[col].isna().all():
        self.add_paragraph_red('该列为空')
        continue

      self.add_normal_p(f'字段类型：{self.df[col].dtype}')
      self.add_table_from_df(describe_auto(self.df, col), True)

      # 为数值型的列绘制频率分布直方图
      if self.df[col].dtype in (float, int):
        self.add_hist_from_data(
            self.df[~self.df[col].isna()][col].values, True
        )
      # 当列的类型为非数值和日期型时，推断可能的类型
      if self.df[col].dtype not in (float, int, 'datetime64[ns]'):
        if text := suspect_series_type(self.df, col):
          self.add_paragraph_red(text)

  def examine_all(self, file_path):
    """整套流程"""
    self.preprocess()
    self.basic()
    self.col_by_col()
    self.save(file_path=file_path)
