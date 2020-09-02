# encoding:GBK
import os

import pandas as pd
from ricco.dtxm.basic_tools import _Tools
from ricco.util import fn


class Dtexm(_Tools):

    def basic(self):
        '''数据基础信息描述'''
        # 列名
        self.add_bullet_list('列名：')
        self.add_normal_p('，'.join(self.df.columns))
        # 文件size
        self.add_bullet_list('文件尺寸：')
        self.add_normal_p(f'行：{self.df.shape[0]}，列{self.df.shape[1]}')
        # 列类型
        self.add_bullet_list('数据类型：')
        self.col_types = pd.DataFrame(self.df.dtypes, columns=['类型']).reset_index().rename(columns={'index': '列名'})
        self.add_df2table(self.col_types)

    def col_by_col(self):
        '''逐列检测'''
        for col in self.df.columns:
            self.add_bullet_list(col)
            if (self.df[col].dtype == 'int64') | (self.df[col].dtype == 'float64'):
                self.serise_describe(col)
                self.hist_plot(col)
                self.add_normal_p('')
            elif (self.df[col].dtype == 'O'):
                self.object_describe(col)
                self.is_float(col)
                self.is_date(col)
                self.add_normal_p('')


    def save(self, savefilename: str = None):
        '''保存文件至word文档'''
        if savefilename == None:
            if isinstance(self.filename, pd.DataFrame):
                raise FileNotFoundError('请输入要保存的文件路径')
            savefilename = fn(self.filename) + '-检测报告.docx'
        self.doc.save(savefilename)
        print('文件保存至', os.path.abspath(savefilename))

    def examine_all(self, savefilename: str = None):
        '''整套流程'''
        self.basic()
        self.col_by_col()
        self.save(savefilename=savefilename)


if __name__ == '__main__':
    doc = Dtexm('成交2.xlsx')
    doc.examine_all()
