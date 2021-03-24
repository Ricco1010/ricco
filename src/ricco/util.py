import csv
import datetime
import os
import re
import warnings
import zipfile

import geopandas as gpd
import numpy
import pandas as pd
from shapely import wkb
from tqdm import tqdm

from ricco.config import UTIL_CN_NUM


def ext(filepath):
    """扩展名"""
    return os.path.splitext(filepath)[1]


def fn(filepath):
    """路径及文件名（不含扩展名）"""
    return os.path.splitext(filepath)[0]


def max_grid():
    """防止单个单元格文件过大而报错"""
    import sys
    maxint = sys.maxsize
    decrement = True
    while decrement:
        decrement = False
        try:
            csv.field_size_limit(maxint)
        except OverflowError:
            maxint = int(maxint / 10)
            decrement = True


def versionCompare(smaller: str, bigger: str, n=3):
    lis1 = smaller.split('.')
    lis2 = bigger.split('.')
    lis1 = [to_float(i) for i in lis1]
    lis2 = [to_float(i) for i in lis2]
    for i in range(n):
        if lis1[i] > lis2[i]:
            return False
    return True


def rdxls(filename, sheet_name=0, sheet_contains: str = None, errors='raise'):
    """
    读取excel文件

    :param filename: 文件名
    :param sheet_name: sheet表的名称
    :param sheet_contains: sheet表包含的字符串
    :param errors: 当没有对应sheet时，raise: 抛出错误, coerce: 返回空的dataframe
    :return:
    """
    if sheet_name == 0:
        if sheet_contains is not None:
            df = pd.read_excel(filename, sheet_name=None)
            sheet_list = [i for i in df.keys() if sheet_contains in i]
            if len(sheet_list) != 0:
                sheet_name = sheet_list[0]
                if len(sheet_list) == 1:
                    print(f"sheet:  <'{sheet_name}'>")
                elif len(sheet_list) >= 2:
                    warnings.warn(f"包含'{sheet_contains}'的sheet有{sheet_list}，所读取的sheet为:{sheet_name}")
                return df[sheet_name]
            else:
                if errors == 'coerce':
                    warnings.warn(f'没有包含{sheet_contains}的sheet，请检查')
                    return pd.DataFrame()
                elif errors == 'raise':
                    raise ValueError(f'没有包含{sheet_contains}的sheet，请检查')
                else:
                    raise KeyError("参数'error'错误, 可选参数为coerce和raise")
    else:
        print(f"sheet:  <'{sheet_name}'>")
    return pd.read_excel(filename, sheet_name=sheet_name)


def rdf(file_path: str, sheet_name=0, sheet_contains: str = None) -> pd.DataFrame:
    """
    常用文件读取函数，支持.csv/.xlsx/.shp

    :param file_path: 文件路径
    :param sheet_name: 指定sheet表名称，只对excel生效
    :param sheet_contains: sheet表包含的字符串，只对excel生效
    :return: dataframe
    """
    max_grid()
    if ext(file_path) == '.csv':
        try:
            df = pd.read_csv(file_path, engine='python', encoding='utf-8-sig')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, engine='python')
    elif ext(file_path) in ('.xls', '.xlsx'):
        df = rdxls(file_path, sheet_name=sheet_name, sheet_contains=sheet_contains)
    elif ext(file_path) == '.shp':
        try:
            df = gpd.GeoDataFrame.from_file(file_path)
        except UnicodeEncodeError:
            df = gpd.GeoDataFrame.from_file(file_path, encoding='GBK')
    else:
        raise Exception('未知文件格式')
    return df


def read_linejson(filename, encoding='utf-8'):
    """
    逐行读取json格式的文件，目前用于金刚石数据读取

    :param filename: 文件名
    :param encoding: 文件编码，默认为utf-8
    :return:
    """
    import json
    records = []
    with open(filename, 'r', encoding=encoding) as file:
        for line in file:
            row = json.loads(line)
            records.append(row)
    return pd.DataFrame(records)


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


def plate_format(filename, name_col='板块', plate_name=True, save=False):
    """
    自动处理板块名

    :param filename: 文件路径
    :param name_col: 有板块名的列
    :param plate_name: 是否增加“板块名”这一列
    :return:
    """
    if plate_name:
        if '脉策板块' not in filename:
            warnings.warn('非脉策板块不应该有板块名，请确认是否正确', UserWarning)
    else:
        if '脉策板块' in filename:
            warnings.warn('脉策板块应该有板块名，请确认是否正确', UserWarning)
    df = rdf(filename)
    valid_check(df)
    df['name'] = df[name_col]
    df['板块'] = df[name_col]
    df['板块名'] = df[name_col]
    if plate_name:
        df = df[['name', '板块', '板块名', 'geometry']]
    else:
        df = df[['name', '板块', 'geometry']]
    if save:
        df.to_csv(filename, index=False, encoding='utf-8')
    return df


def ensure_lnglat(df) -> pd.DataFrame:
    """将df中的经纬度重命名为lng和lat"""
    from ricco import to_lnglat_dict
    df.rename(columns=to_lnglat_dict, inplace=True)
    if ('lng' not in df.columns) or ('lat' not in df.columns):
        warnings.warn('转换失败，输出结果无lng或lat字段')
    return df


def read_and_rename(file: str) -> pd.DataFrame:
    """读取文件并将经纬度统一为lng和lat，并按照经纬度排序"""
    df = rdf(file)
    df = ensure_lnglat(df)
    if 'lat' in df.columns:
        df.sort_values(['lat', 'lng'], inplace=True)
        df = df.reset_index(drop=True)
    return df


def reset2name(df: pd.DataFrame, origin: bool = False) -> pd.DataFrame:
    """
    重置索引，并重命名为name， 默认将索引重置为有序完整的数字（重置两次）

    :param df:
    :param origin: 为True时，将原来的索引作为name列（重置一次）
    """
    if not origin:
        df = df.reset_index(drop=True)
    df = df.reset_index().rename(columns={'index': 'name'})
    return df


def to(filename: str, res_type: str = 'utf-8-sig'):
    """
    快速转文件格式

    :param filename: 文件名
    :param res_type: 文件类型，支持参数：'excel', '.xls', '.xlsx', 'xls', 'xlsx', 'utf-8', 'utf-8-sig', 'gbk'
    :return:
    """
    temp = 'temp_haibara.csv'
    if os.path.exists(temp):
        os.remove(temp)
    if res_type in ('excel', '.xls', '.xlsx', 'xls', 'xlsx'):
        rdf(filename).to_excel(fn(filename) + '.xlsx', index=False)
    elif res_type in ('utf-8', 'utf-8-sig', 'gbk'):
        if res_type in ('gbk', 'GBK'):
            try:
                rdf(filename).to_csv(temp, index=False, encoding=res_type)
                os.remove(temp)
            except UnicodeEncodeError:
                raise KeyError('此数据无法使用gbk编码，请更换utf-8或utf-8-sig')
        rdf(filename).to_csv(fn(filename) + '.csv', index=False, encoding=res_type)
    else:
        raise KeyError('不能识别的res_type类型')


def pinyin(word: str) -> str:
    """将中文转换为汉语拼音"""
    import pypinyin
    if isinstance(word, str):
        s = ''
        for i in pypinyin.pinyin(word, style=pypinyin.NORMAL):
            s += ''.join(i)
    else:
        raise TypeError('输入参数必须为字符串')
    return s


def mkdir_2(path: str):
    """新建文件夹，忽略存在的文件夹"""
    if not os.path.isdir(path):
        os.makedirs(path)


def dir2zip(filepath, delete_exist=True, delete_origin=False):
    """压缩文件夹"""
    zipfilename = filepath + '.zip'
    if delete_exist:
        if os.path.exists(zipfilename):
            os.remove(zipfilename)
            print(f'文件已存在，delete {zipfilename}')
    print(f'saving {zipfilename}')
    z = zipfile.ZipFile(zipfilename, 'w', zipfile.ZIP_DEFLATED)
    for dirpath, dirnames, filenames in os.walk(filepath):
        for filename in filenames:
            filepath_out = os.path.join(dirpath, filename)
            filepath_in = os.path.join(os.path.split(dirpath)[-1], filename)
            z.write(filepath_out, arcname=filepath_in)
    z.close()
    if delete_origin:
        print(f'delete {filepath}')
        del_file(filepath)


def del_file(filepath):
    """
    删除某一目录下的所有文件或文件夹
    :param filepath: 路径
    :return:
    """
    import shutil
    del_list = os.listdir(filepath)
    for f in del_list:
        file_path = os.path.join(filepath, f)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    shutil.rmtree(filepath)


def zip_format_dir(root_dir, pattern=r'.*Update20\d{6}', delete_origin=False):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if re.match(pattern, dirpath):
            dir2zip(dirpath, delete_origin=delete_origin)


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


def per2float(string: str) -> float:
    """带有百分号的数值字符串转小数点形式的数值，
    没有百分号的返回原值"""
    if '%' in string:
        string = string.rstrip('%')
        return float(string) / 100
    else:
        return float(string)


def extract_num(string: str,
                num_type: str = 'str',
                method: str = 'list',
                join_list: bool = False,
                ignore_pct: bool = True,
                multi_warning=False):
    """
    提取字符串中的数值，默认返回所有数字组成的列表

    :param string: 输入的字符串
    :param num_type:  输出的数字类型，int/float/str，默认为str
    :param method: 结果计算方法，对结果列表求最大/最小/平均/和等，numpy方法，默认返回列表本身
    :param join_list: 是否合并列表，默认FALSE
    :param ignore_pct: 是否忽略百分号，默认True
    :param multi_warning:
    :return:
    """
    string = str(string)
    if ignore_pct:
        lis = re.findall(r"\d+\.?\d*", string)
    else:
        lis = re.findall(r"\d+\.?\d*%?", string)
    lis2 = [getattr(numpy, num_type)(per2float(i)) for i in lis]
    if len(lis2) > 0:
        if method != 'list':
            if join_list:
                raise ValueError("计算结果无法join，只有在method='list'的情况下, 才能使用join_list=True")
            if multi_warning & (len(lis2) >= 2):
                warnings.warn(f'有多个值进行了{method}运算')
            res = getattr(numpy, method)(lis2)
        else:
            if num_type == 'str':
                res = ['{:g}'.format(float(j)) for j in lis2]
            else:
                res = lis2
            if join_list:
                res = ''.join(res)
    else:
        res = None
    return res


def to_float(string,
             rex_method: str = 'mean',
             ignore_pct: bool = False,
             multi_warning=True):
    """
    字符串转换为float
    """
    return extract_num(string,
                       num_type='float',
                       method=rex_method,
                       ignore_pct=ignore_pct,
                       multi_warning=multi_warning)


def serise_to_float(serise: pd.Series, rex_method: str = 'mean'):
    """
    pandas.Series: str --> float

    :param serise: 要转换的pandas列
    :param rex_method: 计算mean,max,min， 默认为mean
    """
    return serise.apply(lambda x: to_float(x, rex_method=rex_method))


def date_to(serise: pd.Series, mode: str = 'first'):
    """
    将日期转为当月的第一天或最后一天

    :param serise: pd.Serise
    :param mode: 'first' or 'last'
    :return:
    """
    from pandas.tseries.offsets import MonthEnd

    def trans(x):
        if x is not pd.NaT:
            y = int(x.year)
            m = int(x.month)
            d = int(x.day)
            return datetime.datetime(y, m, d)
        else:
            return None

    serise = pd.to_datetime(serise)
    if mode == 'first':
        serise = serise.apply(lambda x: x.replace(day=1))
    elif mode == 'last':
        serise = pd.to_datetime(serise, format="%Y%m") + MonthEnd(1)
    else:
        raise ValueError(f"{mode}不是正确的参数，请使用 'first' or 'last'")
    serise = serise.apply(trans)
    return serise


def excel2date(dates):
    """excel的数字样式时间格式转日期格式"""
    if len(str(dates)) == 5:
        try:
            dates = int(dates)
            delta = datetime.timedelta(days=dates)
            today = datetime.datetime.strptime('1899-12-30', '%Y-%m-%d') + delta
            dates_ = datetime.datetime.strftime(today, '%Y-%m-%d')
            return dates_
        except ValueError:
            return None
    else:
        return dates


def house_type_format(x):
    """
    通过正则表达式将户型统一修改为1房，2房···5房及以上，目前只支持9室以下户型，
    其中5室及以上的类别为“5房及以上”
    """
    exp = '|'.join(UTIL_CN_NUM.keys())
    pattern = f'([{exp}|\d])[室|房]'
    res = re.findall(pattern, str(x))
    if len(res) >= 1:
        res_num = res[0]
        for i in UTIL_CN_NUM:
            res_num = res_num.replace(i, UTIL_CN_NUM[i])
        if int(res_num) <= 4:
            return res_num + '房'
        else:
            return '5房及以上'
    else:
        return None


def best_unique(df: pd.DataFrame,
                key_cols: (list, str),
                value_cols: (str, list) = None,
                filter=False,
                drop_if_null='all'):
    """
    优化的去重函数：
      为保证数据的完整性，去重时优先去除指定列中的空值

    :param df:
    :param key_cols: 按照哪些列去重
    :param value_cols: 优先去除那些列的空值，该列表是有顺序的
    :param filter:
    :param drop_if_null: 如何处理value_cols内值为空的列；'all'：都为空时删除该列，'any'：任意一列为空时就删除，None：保留空白
    :return:
    """
    key_cols = ensure_list(key_cols)
    if value_cols is None:
        value_cols = [i for i in df.columns if i not in key_cols]
    else:
        value_cols = ensure_list(value_cols)
    if drop_if_null is not None:
        df = df.dropna(subset=value_cols, how=drop_if_null).dropna(subset=key_cols, how='all')
    df = df.sort_values(value_cols, na_position='first')
    df = df.drop_duplicates(key_cols, keep='last').reset_index(drop=True)
    if filter:
        df = df[key_cols + value_cols]
    return df


def ensure_list(val):
    """将标量值和Collection类型都统一转换为LIST类型"""
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, (set, tuple)):
        return list(val)
    return [val]


def update_df(df: pd.DataFrame,
              new_df: pd.DataFrame,
              on: (str, list) = None,
              mode='update'):
    """
    根据某一列更新dataframe里的数据

    :param df: 待升级的
    :param new_df: 新表
    :param on: 根据哪一列升级,默认为None，使用index
    :param mode：处理方式，update：直接更新对应位置的数值，insert：只有对应位置为空时才更新
    :return:
    """
    v1 = len(df)
    if on is not None:
        on = ensure_list(on)
        new_df = new_df.drop_duplicates()
        if any(new_df[on].duplicated()):
            raise ValueError('new_df中有重复的索引列对应不同的值，请检查')
        new_df = df[on].drop_duplicates().merge(new_df, how='inner', on=on)
        df = df.set_index(on, drop=False)
        new_df = new_df.set_index(on, drop=False)
    if mode == 'update':
        df.update(new_df)
    elif mode == 'insert':
        df = df.combine_first(new_df)
    else:
        raise ValueError(f'参数{mode}错误,可选参数为 update or insert')
    df = df.reset_index(drop=True)
    if on is not None:
        if v1 != len(df):
            raise ValueError('update后Dataframe结构发生变化，请检查')
    return df


def segment(x,
            gap: (list, float, int),
            sep: str = '-',
            unit: str = '',
            bottom: str = '以下',
            top: str = '以上') -> str:
    """
    区间段划分工具

    :param x: 数值
    :param gap: 间隔，固定间隔或列表
    :param unit: 单位，末尾
    :param sep: 分隔符，中间
    :param bottom: 默认为“以下”：80米以下
    :param top: 默认为“以上”：100米以上
    :return: 区间段 'num1分隔符num2单位'：‘80-100米’
    """

    def between_list(_x, lis):
        for i in reversed(range(len(lis) - 1)):
            if _x >= lis[i]:
                return lis[i], lis[i + 1]

    x = to_float(x)
    if x is None:
        return ''
    elif isinstance(gap, list):
        gap = sorted(list(set(gap)))
        if x < gap[0]:
            return f'{gap[0]}{unit}{bottom}'
        elif x >= gap[-1]:
            return f'{gap[-1]}{unit}{top}'
        else:
            return f'{between_list(x, gap)[0]}{sep}{between_list(x, gap)[1]}{unit}'
    elif isinstance(gap, (int, float)):
        if x >= 0:
            return f'{int(x / gap) * gap}{sep}{int(x / gap) * gap + gap}{unit}'
        else:
            return f'{int(x / gap) * gap - gap}{sep}{int(x / gap) * gap}{unit}'
    else:
        raise TypeError('gap参数数据类型错误')


def format_range(s: str, sep: str = None):
    """
    将分段解析为由断点值组成的tuple

    example：

    >>>format_range("111~222")

    (111, 222)

    >>>format_range("~111")

    (None, 111)

    :param s: 要解析的分段字符串
    :param sep: 自定义分隔符
    :return:
    """
    if sep is None:
        sep_list = ['|', '~', ',', '-']
        for sep in sep_list:
            if sep in s:
                break
    if sep not in s:
        raise ValueError('默认分隔符无法分割字段，请定义分隔符')
    s_list = s.split(sep)
    if len(s_list) == 2:
        return tuple([to_float(i) for i in s_list])
    else:
        raise ValueError('分段解析异常，请检查')


def col_cls(value, _min, _max, _cls):
    """
    值在区间内返回当前类别

    :param value: 值
    :param _min: 区间上限，区间上下限至多有一个为None
    :param _max: 区间下限，区间上下限至多有一个为None
    :param _cls: 符合该区间时的类别名称
    :return:
    """
    if _min == _max:
        if _min is None:
            raise ValueError('区间范围不能同时为None')
        else:
            raise ValueError('区间范围不能相等')
    if _min is None:
        if value < _max:
            return _cls
    elif _max is None:
        if value >= _min:
            return _cls
    else:
        if _min <= value < _max:
            return _cls


def standard(serise: (pd.Series, list),
             q: float = 0.01,
             min_score: float = 0,
             minus: bool = False) -> (pd.Series, list):
    if minus:
        serise = 1 / (serise + 1)
    max_ = serise.quantile(1 - q)
    min_ = serise.quantile(q)
    serise = serise.apply(lambda x: (x - min_) / (max_ - min_) * (100 - min_score) + min_score)
    serise[serise >= 100] = 100
    serise[serise <= min_score] = min_score
    return serise


def col_round(df, col: list):
    """对整列进行四舍五入，默认绝对值大于1的数值保留两位小数，小于1 的保留4位"""

    def _round(x):
        if abs(x) >= 1:
            return round(x, 2)
        else:
            return round(x, 4)

    col = ensure_list(col)
    for i in col:
        df[i] = df[i].apply(lambda x: _round(x))
    return df


def table2dict(df: pd.DataFrame,
               key_col: str = None,
               value_col: (str, list) = None,
               orient: str = 'dict') -> dict:
    """
    DataFrame转字典

    :param df:
    :param key_col: 生成key的列
    :param value_col: 生成value的列
    :param orient: 生成dict的方式，默认'dict',还有 ‘list’, ‘series’, ‘split’, ‘records’, ‘index’
    :return:
    """
    if (key_col is None) or (value_col is None):
        cols = list(df.columns).copy()
        key_col = cols[0]
        value_col = cols[1]

    df = df[~df[key_col].isna()]
    df.set_index(key_col, inplace=True)

    if isinstance(value_col, list):
        df = df[value_col]
        return df.to_dict(orient=orient)
    else:
        df = df[[value_col]]
        return df.to_dict(orient=orient)[value_col]


def fuzz_match(string: str, ss: (list, pd.Series)):
    """
    为某一字符串从某一集合中匹配相似度最高的元素

    :param string: 输入的字符串
    :param ss: 要去匹配的集合
    :return: 字符串及相似度组成的列表
    """
    from fuzzywuzzy import fuzz

    def _ratio(_s, x):
        return fuzz.ratio(_s, x), fuzz.partial_ratio(_s, x)

    max_r, max_pr, max_s = 0, 0, None
    for s in ss:
        r, pr = _ratio(s, string)
        if r > max_r:
            max_r = r
            max_pr = pr
            max_s = s
    return max_s, max_r, max_pr


def fuzz_df(df: pd.DataFrame,
            col: str,
            target_serise: (list, pd.Series)) -> pd.DataFrame:
    """
    为DataFrame中的某一列，从某个集合中匹配相似度最高的元素

    :param df: 输入的dataframe
    :param col: 要匹配的列
    :param target_serise: 从何处匹配， list/pd.Serise
    :return:
    """
    df[[f'{col}_target',
        'normal_score',
        'partial_score']] = df.apply(lambda x: fuzz_match(x[col], target_serise),
                                     result_type='expand', axis=1)
    return df


def plate_pivot_table(df, name_col, labelx, labely):
    """
    基于板块两个标签做透视表，枚举板块名

    :param df: 输入的dataframe，包含字段：板块名及两种字符串型标签
    :param name_col: 有板块名的列
    :param labelx: 输出表横向标签
    :param labely: 输出表纵向标签
    :return:
    """
    df_res1 = df[[name_col, labelx, labely]]
    df_res2 = pd.pivot_table(df_res1, index=labelx, columns=labely, values=[name_col], aggfunc='count')
    df_res2.columns = [col[1] for col in df_res2.columns.values]
    df_res3 = df_res1.groupby([labelx, labely], as_index=False)[name_col].count()
    df_res4 = df_res2.reset_index().copy()
    for i in df_res4.columns[1:]:
        df_res4[i] = df_res4[i].replace(numpy.nan, '').astype('str')
    for i in df_res3.index:
        m = df_res3[labelx][i]
        n = df_res3[labely][i]
        df_res4[n][df_res4[labelx] == m] = '\n'.join(
            df_res1[(df_res1[labelx] == m) & (df_res1[labely] == n)][name_col].to_list())
    return df_res4


# 地理处理
def get_epsg(city):
    """
    查找citycode，用于投影
    """
    from ricco.config import epsg_dict
    if city in epsg_dict.keys():
        return epsg_dict[city]
    else:
        city = city + '市'
        if city in epsg_dict.keys():
            return epsg_dict[city]
        else:
            warnings.warn("获取城市epsg失败，当前默认为32651。请在config.py中补充该城市")
            return 32651


def _loads(x, hex=True):
    from shapely.wkb import loads
    warnings.filterwarnings('ignore', 'Geometry column does not contain geometry.', UserWarning)
    try:
        x = loads(x, hex=hex)
    except AttributeError:
        x = None
    return x


def _dumps(x, hex=True, srid=4326):
    from shapely.wkb import dumps
    try:
        if versionCompare(gpd.__version__, '0.7.2'):
            x = dumps(x, hex=hex, srid=srid)
        else:
            x = dumps(x, hex=hex)
    except AttributeError:
        x = None
    return x


def valid_check(polygon_geom, log=True):
    """检验面的有效性"""
    df = polygon_geom.copy()
    if any(df['geometry'].isnull()):
        raise ValueError('geometry中有空值，请检查')
    df = gpd.GeoDataFrame(df)
    df['geometry'] = df['geometry'].apply(lambda x: _loads(x, hex=True))
    df.crs = 'epsg:4326'
    if not all(df['geometry'].is_valid):
        raise ValueError('有效性检验失败，请确认以下index行是否为有效面{}'.format(df[~df['geometry'].is_valid].index.tolist()))
    if all(~df.geom_type.str.contains('Multi')):
        if log:
            print('Validity test passed.')
    else:
        warnings.warn('文件包含多部件要素,请确认以下index行是否为多部件要素{}'.format(df[df.geom_type.str.contains('Multi')].index.tolist()))


def shp2csv(shpfile_name: str, encoding='utf-8'):
    """shapefile 转 csv 文件"""
    df = rdf(shpfile_name)
    print(df.head())
    df = gpd.GeoDataFrame(df)
    df['geometry'] = df['geometry'].apply(lambda x: _dumps(x, hex=True, srid=4326))
    df.crs = 'epsg:4326'
    save_path = fn(shpfile_name) + '.csv'
    print(df.head())
    try:
        valid_check(df)
    except ValueError:
        warnings.warn('有效性检验失败，可能影响数据上传')
    df.to_csv(save_path, encoding=encoding, index=False)


def csv2shp(filename: str):
    """csv文件 转 shapefile"""
    import fiona
    df = rdf(filename)
    df = df.rename(columns={'名称': 'name',
                            'geom': 'geometry'})
    df = gpd.GeoDataFrame(df)
    df['geometry'] = df['geometry'].apply(lambda x: _loads(x, hex=True))
    df.crs = 'epsg:4326'
    save_path = fn(filename) + '.shp'
    try:
        df.to_file(save_path, encoding='utf-8')
    except fiona.errors.SchemaError:
        df.columns = [pinyin(i) for i in df.columns]
        df.to_file(save_path, encoding='utf-8')
        warnings.warn('已将列名转为汉语拼音进行转换')


def _geom_wkb2lnglat(df, geometry='geometry', delete=False):
    """geometry转经纬度，求中心点经纬度"""
    warnings.filterwarnings('ignore', 'Geometry is in a geographic CRS', UserWarning)
    df = gpd.GeoDataFrame(df)
    df[geometry] = df[geometry].apply(lambda x: _loads(x, hex=True))
    df.crs = 'epsg:4326'
    df['lng'] = df.centroid.x
    df['lat'] = df.centroid.y
    df[geometry] = df[geometry].apply(lambda x: _dumps(x, hex=True, srid=4326))
    if delete:
        df.drop(geometry, axis=1, inplace=True)
    return df


def geom_wkb2lnglat(df,
                    geometry='geometry',
                    delete=False,
                    name_col='name',
                    inter_check=False,
                    fix=False):
    """
    求中心点经纬度，可检验并修复中心点是否在面内

    :param df:
    :param geometry: geometry列的列名，默认为'geometry'
    :param delete:是否删除'geometry'列，默认False
    :param name_col:哪一列作为检验点面关系的索引列，默认为'name'
    :param inter_check:是否检验点是否在面内，默认False
    :param fix:是否修复不在面内的中心点
    :return:
    """
    from ricco.gis_tools import mark_tags_df

    if not inter_check:
        return _geom_wkb2lnglat(df, geometry=geometry, delete=delete)
    else:
        df = _geom_wkb2lnglat(df)
        df_c = df[[name_col, 'lng', 'lat']]
        df_p = df[[name_col, geometry]].rename(columns={name_col: name_col + '_temp'})
        df_c = mark_tags_df(df_c, df_p, col_list=[name_col + '_temp'])
        col_list = df_c[df_c[name_col] != df_c[name_col + '_temp']][name_col].to_list()
        if not all(iter(df_c[name_col] == df_c[name_col + '_temp'])):
            if fix:
                df.loc[df[name_col].isin(col_list), 'lng'] = df[geometry].apply(
                    lambda p: _loads(p).representative_point().x)
                df.loc[df[name_col].isin(col_list), 'lat'] = df[geometry].apply(
                    lambda p: _loads(p).representative_point().y)
                warnings.warn(f'{name_col}为{col_list}的行存在中心点不在面内的情况，已修复')
                return df
            else:
                warnings.warn(f'{name_col}为{col_list}的行存在中心点不在面内的情况，未修复')
        if delete:
            df.drop(geometry, axis=1, inplace=True)
        return df


def geom_wkt2wkb(df, geometry='geometry', epsg_code: int = 4326):
    """wkb转wkt"""
    from shapely import wkb
    from shapely import wkt
    df[geometry] = df[geometry].apply(lambda x: wkt.loads(x))
    df = gpd.GeoDataFrame(df, geometry=geometry, crs=epsg_code)
    df[geometry] = df[geometry].apply(lambda x: wkb.dumps(x, hex=True, srid=epsg_code))
    return df


def geom_wkb2gpd(df, geometry='geometry', epsg_code: int = 4326):
    """
    wkb直接转Dataframe

    :param df:
    :param geometry:
    :param epsg_code:
    :return:
    """
    df[geometry] = df[geometry].apply(_loads)
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=epsg_code)
    return gdf


def point_to_geo(df, lng='lng', lat='lat', delt=1, epsg_code: int = 4326):
    """包含经纬度的DataFrame转GeoDataFrame"""
    from geopandas import points_from_xy
    df = gpd.GeoDataFrame(df, geometry=points_from_xy(df[lng], df[lat]), crs=epsg_code)
    if delt == 1:
        del df[lng]
        del df[lat]
    return df


def point_to_geo_old(df, lng, lat, delt=1):
    """包含经纬度的DataFrame转GeoDataFrame"""
    from shapely.geometry import Point
    df['geometry'] = gpd.GeoSeries(list(zip(df[lng], df[lat]))).apply(Point)
    df = gpd.GeoDataFrame(df)
    df.crs = 'epsg:4326'
    if delt == 1:
        del df[lng]
        del df[lat]
    return df


def lnglat2geom(df, lng='lng', lat='lat', delete=False, code=4326):
    """经纬度转wkb格式的geometry"""
    if (lng in df.columns) & (lat in df.columns):
        df = ensure_lnglat(df)
    df = point_to_geo(df, lng, lat, delt=0, epsg_code=code)
    df['geometry'] = df['geometry'].apply(lambda x: _dumps(x, hex=True, srid=code))
    if delete:
        df.drop(['lng', 'lat'], axis=1, inplace=True)
    else:
        df = df.rename(columns={'lng': lng, 'lat': lat})
    return df


def calcu_area(df, city, area_col='area', force_update=True, unit='km2'):
    """
    计算面文件面积，输入为Dataframe,新增或更新面积字段

    :param city：所在城市，设定投影带，默认为上海市32651；
    :param area_col：面积字段列名，默认为'area';
    :param force_update: 当设定area_col已存在时，是否强制更新面积字段，默认为True;
    :param unit: 可选参数'km', 'km2':平方千米；'m', 'm2'：平方米；
    """

    def area(geom, unit=unit):
        gs = _loads(geom)
        gs = gpd.GeoSeries(gs)
        gs.crs = 'epsg:4326'
        gs = gs.to_crs(epsg=get_epsg(city))
        if unit in ('km2', 'km'):
            area = gs.area / 1000000
        elif unit in ('m2', 'm'):
            area = gs.area
        else:
            raise ValueError(f'面积单位参数错误(当前unit:{unit}),请修正单位为km2/km/m2/m')
        return area[0]

    if isinstance(df, pd.DataFrame):
        valid_check(df)
        if (area_col in df.columns) and (not force_update):
            warnings.warn(f'面积列{area_col}已存在，暂未更新')
        else:
            df[area_col] = df['geometry'].apply(area)
    else:
        raise ValueError('输入参数必须为dataframe，请检查')
    return df


def check_before_upload(filename, save=False):
    """
    上传数据中心之前对文件进行检查

    :param filename:文件路径
    :param save: 是否保存文件，默认为False，当为True时会替换原有文件
    :return:
    """
    df = rdf(filename)
    df = df.rename(columns={'省/直辖市': '省', '区县/县级市': '区县'})
    df = df.rename(columns={'经度': 'lng', '纬度': 'lat'})
    for i in ['id', 'ID', 'Id']:
        if i in df.columns:
            df = df.drop([i], axis=1)
            warnings.warn('表中存在id列，已删除')

    if 'geometry' in df.columns:
        valid_check(df)
        if 'lng' in df.columns:
            df = df.drop(['lng', 'lat'], axis=1)
            print('----------------删除多余的经纬度')
        else:
            print('无多余经纬度')
    elif 'lng' in df.columns:
        if len(df) > 500000:
            df = point_to_geo(df, 'lng', 'lat', delt=1)
            df['geometry'] = df['geometry'].apply(lambda x: _dumps(x, hex=True, srid=4326))
            print('---------------- lng,lat ---> geometry')

    if '更新日期' in df.columns:
        df['更新日期'] = datetime.datetime.now().strftime('%Y-%m-%d')
        df['更新日期'] = pd.to_datetime(df['更新日期'])

    if '添加日期' in df.columns:
        df.drop('添加日期', axis=1, inplace=True)
        print('---------------------删除添加日期')

    if '配套_' in filename:
        if 'name' in df.columns:
            df.drop('name', axis=1, inplace=True)
        if '名称' in df.columns:
            df.drop('名称', axis=1, inplace=True)
        df = reset2name(df)
    if save:
        df.to_csv(filename, index=False, encoding='utf-8')
        warnings.warn(f'已修复并替换{filename}')
    return df


def get_city_code(city):
    """获取城市代码"""
    from ricco.config import city_code
    if city in city_code.keys():
        return ''.join(['v', str(city_code[city]).zfill(7)])
    else:
        city = city + '市'
        if city in city_code.keys():
            return ''.join(['v', str(city_code[city]).zfill(7)])
        else:
            raise ValueError('获取城市code失败，请在config.py中确认补充该城市')


def bigdata2df(filename: str, chunksize: int = 10000, code: str = "utf-8") -> pd.DataFrame:
    reader = pd.read_table(filename,
                           encoding=code,
                           sep=",",
                           skip_blank_lines=True,
                           iterator=True)
    loop = True
    chunks = []
    while loop:
        try:
            chunk = reader.get_chunk(chunksize)
            chunk.dropna(axis=0, inplace=True)
            chunks.append(chunk)
        except StopIteration:
            loop = False
            print("Iteration is stopped.")
    df = pd.concat(chunks, ignore_index=True, axis=1)
    return df


def bigdata2csv(df: pd.DataFrame, filename: str, code: str = "utf-8", chunksize: int = 10000):
    df_head = pd.DataFrame(columns=df.columns.tolist())
    df_head.to_csv(filename, index=False, encoding=code)
    df = df.reset_index(drop=True)
    num_req = len(df) // chunksize + 1
    for req_index in range(num_req):
        sl = slice(req_index * chunksize, (req_index + 1) * chunksize)
        df_c = df.iloc[sl]
        df_c.to_csv(filename, index=False, encoding=code, mode='a', header=False)


def projection(gdf, proj_epsg: int = None, city: str = None):
    if not proj_epsg:
        if not city:
            raise ValueError('获取投影信息失败，请补充参数:proj_epsg投影的坐标系统的epsg编号或city中国城市名称')
        else:
            proj_epsg = get_epsg(city)
    return gdf.to_crs(epsg=proj_epsg)


def getxy_proj(df: pd.DataFrame,
               proj_epsg: int = None,
               city: str = None,
               new_x: str = 'x',
               new_y: str = 'y',
               curr_epsg: int = 4326):
    """
    利用城市名或投影坐标epsg编号，获得数据投影后或坐标系转后的中心点x、y坐标，但原始地理数据信息不变

    :param df: 含地理信息的数据，一定要有geometry 或 lng和lat
    :param proj_epsg: 要投影或转化的坐标的epsg编号
    :param city: 要投影的城市名
    :param new_x: 投影后x坐标的列名
    :param new_y: 投影后y坐标的列名
    :param curr_epsg: 目前数据的坐标系
    :return:
    """
    if 'geometry' in df.columns:
        gdf = geom_wkb2gpd(df, epsg_code=curr_epsg)
    else:
        gdf = point_to_geo(df, epsg_code=curr_epsg)
    gdf = projection(gdf, proj_epsg=proj_epsg, city=city)
    gdf[new_x] = gdf.centroid.x
    gdf[new_y] = gdf.centroid.y
    gdf = projection(gdf, proj_epsg=curr_epsg)
    gdf['geometry'] = gdf['geometry'].apply(lambda x: wkb.dumps(x, hex=True, srid=curr_epsg))
    return gdf
