# encoding:GBK
import geopandas as gpd
import pandas as pd
from ricco import rdf


from . import Base


class Geo_data_process(Base):
    '''地理处理'''

    def to_geo_df(self):
        self.df = gpd.GeoDataFrame(self.df)
        return self.df


class Data_process(Base, Geo_data_process):
    '''Dataframe处理流程'''

    # 列名操作


# if __name__ == '__main__':
# df = rdf('上海土地点位.csv')
# df = '上海土地点位.csv'
#
# a = Data_process(df)
# a.reset2name()
# a.to_gbk('tes2.csv')
# a.rename({})
# a.to_geo_df()
# print(a.df)
