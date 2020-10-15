from ricco import rdf
from ricco import mark_tags_df
from ricco.util import geom_wkb2lnglat


def cls(x, y):
    """客群划分
    根据Z, X, J, Y 和 优享、改善、优选、刚需

    将板块类型划分为
    01_积极增持、02_择优跟进、03_谨慎进入"""
    s1 = '01_积极增持'
    s2 = '02_择优跟进'
    s3 = '03_谨慎进入'
    if x == '优享':
        if y == 'Y':
            return s2
        elif y in ('X', 'J', 'Z'):
            return s1
        else:
            raise ValueError('类别有误')

    elif x == '改善':
        if y == 'Y':
            return s3
        elif y == 'J':
            return s2
        elif y in ('Z', 'X'):
            return s1
        else:
            raise ValueError('类别有误')

    elif x == '优选':
        if y == 'Y':
            return s3
        elif y in ('J', 'X'):
            return s2
        elif y == 'Z':
            return s1
        else:
            raise ValueError('类别有误')

    elif x == '刚需':
        if y in ('Y', 'J'):
            return s3
        elif y == 'X':
            return s2
        elif y == 'Z':
            return s1
        else:
            raise ValueError('类别有误')
    else:
        raise ValueError('类别有误')


def customer_cls(bk_cls, p1=0.5, p2=0.7, p3=0.9):
    """板块客群类型划分
    三个断点分位数p1, p2, p2
    将客群划分为 刚需--p1--优选--p2--改善--p3--优享"""
    bk_cls.loc[bk_cls['平均工资'] < bk_cls['平均工资'].quantile(p1), '客群类型'] = '刚需'

    bk_cls.loc[(bk_cls['平均工资'] >= bk_cls['平均工资'].quantile(p1)) &
               (bk_cls['平均工资'] < bk_cls['平均工资'].quantile(p2)), '客群类型'] = '优选'

    bk_cls.loc[(bk_cls['平均工资'] >= bk_cls['平均工资'].quantile(p2)) &
               (bk_cls['平均工资'] < bk_cls['平均工资'].quantile(p3)), '客群类型'] = '改善'

    bk_cls.loc[bk_cls['平均工资'] >= bk_cls['平均工资'].quantile(p3), '客群类型'] = '优享'

    return bk_cls


def grid2plate(grid, bk, col='分类_住宅'):
    """栅格土地分类聚合到板块"""
    # df = df[['grid_id', col, 'lng', 'lat']]
    if 'lng' not in grid.columns:
        grid = geom_wkb2lnglat(grid)
    df = mark_tags_df(grid, bk, ['板块'])
    gp = df.groupby(['板块', col], as_index=False)['grid_id'].count()
    gp2 = gp.groupby('板块', as_index=False)['grid_id'].max()
    df_m = gp2.merge(gp[['grid_id', col, '板块']], how='left')
    df_m = df_m.drop_duplicates(['grid_id', '板块'])
    df_cls = bk.merge(df_m[['板块', col]])

    df_s = df.groupby(['板块', '分类_住宅'], as_index=False)[['population', 'traffic', 'retail', 'commerce',
                                                        'education', 'healthCare', 'recreation', 'landscape',
                                                        'disadvantage', 'industry']].mean()
    df_cls = df_cls.merge(df_s, on=['板块', '分类_住宅'], how='left')
    return df_cls


def gird2plate_q(grid, bk, q=0.75):
    """grid columns: ['grid_id', '平均工资', 'geometry']"""
    df = grid[['grid_id', '平均工资', 'geometry']]
    df = mark_tags_df(df, bk, col_list=['板块'])
    df = df.groupby('板块', as_index=False)['平均工资'].quantile(q)
    df_m = bk.merge(df, how='left')
    return df_m


def disadv_list(df, ds):
    """将板块市场计算的负面清单添加到底表中"""
    ds = ds[['板块', '负面清单']]
    bk_cls = df.merge(ds, how='left')
    bk_cls['板块分类_修正'] = bk_cls.loc[bk_cls['负面清单'] != '无', '负面清单']
    bk_cls['板块分类_修正'] = bk_cls['板块分类_修正'].replace(
        '无', '').combine_first(bk_cls['板块分类'])
    bk_cls['板块分类_修正'] = bk_cls['板块分类_修正'].replace('去化周期长', '04_负面清单')
    return bk_cls


def test():
    print('3')
