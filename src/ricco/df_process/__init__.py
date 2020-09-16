from ricco import rdf
import pandas as pd
from ricco import reset2name


class Base(object):
    def __init__(self, df):
        if isinstance(df, str):
            self.df = rdf(df)
        elif isinstance(df, pd.DataFrame):
            self.df = df
        else:
            ValueError('请输入Dataframe或路径')

    def reset2name(self):
        '''重置索引列并重命名为name'''
        self.df = reset2name(self.df)
        return self.df

    def rename(self, dic: dict):
        '''重命名列'''
        self.df.rename(columns=dic, inplace=True)
        return self.df

    # 保存文件
    def to_gbk(self, filename: str):
        '''保存coding为gbk的csv文件'''
        self.df.to_csv(filename, index=False, encoding='GBK')
        return self.df

    def to_utf8(self, filename: str):
        '''保存coding为gbk的csv文件'''
        self.df.to_csv(filename, index=False, encoding='utf-8')
        return self.df
