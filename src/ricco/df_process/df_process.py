# encoding:GBK
import pandas as pd
from ricco import rdf
from ricco import reset2name


class BaseTransformer(object):
    def __init__(self, df):
        if isinstance(df, str):
            self.df = rdf(df)
        elif isinstance(df, pd.DataFrame):
            self.df = df
        else:
            ValueError('请输入Dataframe或路径')


class Data_process(BaseTransformer):
    def reset2name(self):
        '''重置索引列并重命名为name'''
        self.df = reset2name(self.df)
        return self.df

    def to_gbk(self, filename: str):
        '''保存coding为gbk的csv文件'''
        self.df.to_csv(filename, index=False, encoding='GBK')
        return self.df

    def rename(self, dic: dict):
        '''重命名列'''
        self.df.rename(columns=dic, inplace=True)
        return self.df


# if __name__ == '__main__':
#     # df = rdf('上海土地点位.csv')
#     df = '上海土地点位.csv'
#
#     a = Data_process(df)
#     a.reset2name()
#     a.to_gbk('tes2.csv')
#     a.rename({})
#
#     print(a.df)
