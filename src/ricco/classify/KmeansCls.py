from ricco.df_process import Base
from sklearn.cluster import KMeans
from warnings import warn


def standard(df, col_list, quantile=0.99):
    def cacul(x, h, l):
        x = round((x - l) / (h - l) * 100, 2)
        if x > 100:
            x = 100
        return x

    for i in col_list:
        h = df[i].quantile(quantile)
        l = df[i].min()
        df[i] = df[i].apply(lambda x: cacul(x, h, l))
    return df


def standard_min(df, col_list, quantile=0.01):
    def cacul(x, h, l):
        x = round((h - x) / (h - l) * 100, 2)
        if x > 100:
            x = 100
        return x

    for i in col_list:
        h = df[i].max()
        l = df[i].quantile(quantile)
        df[i] = df[i].apply(lambda x: cacul(x, h, l))
    return df


class KmeansCls(Base):
    # contxt = '''
    # 设置参数：
    # KmeansCls().city：城市
    # KmeansCls().types：类型标识（可选）
    # KmeansCls().n：分类数目
    # KmeansCls().x_col：参与聚类的全部指标列表
    # KmeansCls().x_col_dis：逆向指标列表（可选，默认没有逆向指标）
    # '''
    # print(contxt)

    n = None
    city = None
    types = ''
    x_col = None
    x_col_dis = []
    if n == None:
        raise ValueError('请设置类别数量：KmeansCls().n')
    if city == None:
        raise ValueError('请设置城市名称：KmeansCls().city')
    if types == '':
        warn('未设置分类标志')
    if x_col == None:
        raise ValueError('请设置参与分类指标列表：KmeansCls().x_col')
    if x_col_dis == []:
        warn('参与计算的指标无逆向指标')

    x_col_adv = x_col.copy()
    for i in x_col_dis:
        x_col_adv.remove(i)

    def standard_df(self):
        for i in self.x_col:
            try:
                self.df[i] = self.df[i].fillna(0)
            except:
                print(i)
        self.df = standard(self.df, self.x_col_adv)
        self.df = standard_min(self.df, self.x_col_dis)
        return self.df

    def kmcls(self):
        self.df = self.df.reset_index(drop=True)
        km = KMeans(n_clusters=self.n)
        km.fit(self.df[self.x_col])
        self.df['label'] = km.labels_
        return self.df

    def score(self):
        df_score = self.df[self.x_col + ['label']].groupby('label').mean()
        df_score['score'] = self.df[self.x_col].mean(axis=1)
        self.df_score = df_score.reset_index()
        df_score = df_score.sort_values('score', ascending=False).reset_index()[['label', 'score']]
        self.df = self.df.merge(df_score, how='left')
        return self.df

    def descrp(self):
        self.df_score = self.df_score.set_index('label').T
        return self.df_score

    def report(self):
        self.kmcls()
        self.score()
        self.descrp()
        self.df.to_csv(f'{self.city}_{self.types}_Kmeans聚类结果_{self.n}类.csv',
                       index=0,
                       encoding='GBK')
        self.df_score.to_csv(f'{self.city}_{self.types}_指标得分均值_{self.n}类.csv',
                             index=0,
                             encoding='GBK')


if __name__ == '__main__':
    km = KmeansCls('沈阳_板块底表_指标.csv')
    km.n = 5
    km.city = '沈阳'
    km.x_col = ['人口得分', '产业得分', '交通得分', '商业得分', '商务得分',
                '教育得分', '医疗得分', '休闲得分', '景观得分', '劣势得分']

    km.report()
