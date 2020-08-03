# Ricco
实用工具包

## Installation
```bash
pip install ricco
```
## Update package
```bash
pip install -i https://pypi.org/pypi ricco --upgrade
```
---
## 函数使用说明
### 文件存取工具
#### 1. 文件读取文件
* func: `rdf(filepath)`
  * 文件读取通用函数
  * 目前支持格式`.csv/.xls/.xlsx/.shp`
  * 示例代码：
    ```python
    from ricco import rdf
    
    filepath = 'data.csv'
    df = rdf(filepath)
    ```
    

#### 2. 拆分文件
* func: `split_csv(filename, n=5)`
  * 将文件拆分为多个同名的csv文件
  * 其中输入文件为`.csv/.xls/.xlsx`
  * 输出文件为`.csv` 
  * 示例代码：
    ```python
    from ricco import split_csv
    
    filename = 'data.csv'
    split_csv(filename, n=2)  # 将文件拆分为两个同名的文件
    ```
    > ./data/
    >> Part_0/
    >>
    >>> data.csv
    >>
    >> Part_1/
    >>
    >>> data.csv
    
    ---
### dataframe及数据处理工具
* func: `reset2name(df)`
  * 将index拿出来作为name列
  * 示例代码：
    ```python
    from ricco import  rdf
    from ricco import reset2name
    
    df = rdf('data.csv')
    df = reset2name(df)
    ```

* func: ```
        extract_num(string: str,
                num_type: str = 'str',
                method: str = 'list',
                join_list: bool = False,
                ignore_pct: bool = True,
                multi_warning=False)```
   
          提取字符串中的数值，默认返回所有数字组成的列表
        :param string: 输入的字符串
        :param num_type:  输出的数字类型，int/float/str，默认为str
        :param method: 结果计算方法，对结果列表求最大/最小/平均/和/等，numpy方法，默认返回列表本身
        :param join_list: 是否合并列表，默认FALSE
        :param ignore_pct: 是否忽略百分号，默认True
        


* func: `to_float(string, rex_method: str = 'mean')`
  * 将字符串转为数字格式，无法转换的为空值，同时支持正则表达式提取数字，支持%格式数据
  * 示例代码：
    ```python
    from ricco import to_float
    
    to_float('10%')
    # 0.1
    to_float('10--')
    # 10.0
    ```
* func: `serise_to_float(serise)`
  * pandas.Series: str --> float
  
 
 * func: `segment(x, gap, sep: str = '-', unit: str = '')`
   * 区间段划分工具
   * `x`: 输入的数值
   * `gap`: 数值：划分间隔；list：自定义分段
   * `sep`: 分隔符，默认为'-' 
   * `unit`: 分段末尾的单位，如米、元等
   * 示例代码：
   
    ```python
    from ricco import segment
    
    segment(55, 20, sep='-', unit='米')
    # 40-60米
    segment(55, 20)
    # '40-60'
    segment(55, 20, sep='--', unit='米') 
    # '40--60米'
    segment(55, [20]) 
    # '20以上'
    segment(10, [20, 50], unit='米') 
    # '20米以下'
    segment(20, [20, 50], unit='米') 
    # '20-50米'
    segment(50, [20, 50], unit='米') 
    # '50米以上'
    ```
---


### 文件转换工具
* func: `csv2shp('filename.csv')`
  * csv文件转shapefile，必须要有geometry字段
  * 由于列名为中文转换失败的会转化为汉语拼音去转换
* func: `shp2csv('shapefilename.shp')`
  * shapefile转csv
---
### 坐标转换和地址解析
* func: `BD2WGS(df)`
  * bd09（百度） --> wgs84，经纬度必须为lng和lat
  * 示例代码：
    ```python
    from ricco import BD2WGS
    
    df = BD2WGS(df)
    ```
    
* func: `GD2WGS(df)`
  * gcj02（高德） --> wgs84，经纬度必须为lng和lat
  * 示例代码：
    ```python
    from ricco import GD2WGS
    
    df = GD2WGS(df)
    ```

* func: `get_lnglat(addr: str, addr_type: str, city: str = '')`
  * geocoding工具，通过地址或项目名称，返回经纬度（wgs84）
  * `addr`: 地址或经纬度
  * `addr_type`: 地址的类型，可选`'addr'`(地址类型：xx路xx号)或`'name'`（项目名称：XX大厦）
  * `city`: 城市
  *示例代码
    ```python
    from ricco.geocode_bd import get_lnglat
    
    get_lnglat('脉策数据', addr_type='name', city='上海')
    # [121.516868, 31.311847, '上海脉策数据科技有限公司']
    
    get_lnglat('政学路51号', addr_type='addr', city='上海')
    # [121.5166918714937, 31.31181948447693, None]
    ```

* func: `geocode_df(df, addr_col, addr_type: str, city: str = '')`
  * 针对dataframe批量解析经纬度
  * `df`: 输入的dataframe
  * `addr_col`: 作为地址去解析的列名，可传入列名的列表，列表中的元素是有顺序的，如`['区县', '项目名称']`
  * `addr_type`: 地址的类型，可选`'addr'`(地址类型：xx路xx号)或`'name'`（项目名称：XX大厦）
  * `city`: 城市
---


### 空间计算工具
* func: `valid_check`
  * 检查面文件的有效性
* func: `circum_pio_num_geo_aoi`
  * 空间计算
* func: `mark_tags_df`
  * 通过面给点位打标签
---
### 其他工具
* func: `mkdir_2`
  * 新建文件夹，已有的文件夹不再新建
* func: `pinyin`
  * 中文转汉语拼音
  * 示例代码：
    ```python
    from ricco import pinyin
    
    pinyin('测试')
    # ceshi
    ```









