# Ricco
常用工具包

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

* func: `extract_num(string, num_type='str', method='', join_list=False)`
  * 使用正则表达式提取字符串中的数字
  * `num_type`：返回的列表中的数字格式，可选：int, float, str
  * `method`：对列表中的数字进行计算，得到唯一值，可选：max, min, mean, sum
  * `join_list`：是否对列表中的字符串进行拼接，True or False
* 示例代码：
```python
from ricco import extract_num

extract_num('---1231```93.22dddd')
# ['1231', '93.22']
extract_num('---1231```93.22dddd', join_list=True)
# '123193.22'
extract_num('---1231```93.22dddd', num_type='float')
# [1231.0, 93.22]
extract_num('---1231```93.22dddd', num_type='int')
# [1231, 93]
extract_num('---1231```93.22dddd', num_type='int',method='mean')
# 662.0
```

* func: `to_float(string, rex: bool = False, rex_method: str = 'mean', rex_warning: bool = True)`
  * 将字符串转为数字格式，无法转换的为空值，同时支持正则表达式提取数字，支持%格式数据
  * `rex`：是否适用正则表达式
  * `rex_method`：正则表达式参数，参考extract()中method
  * `rex_warning`：可忽略使用方法的警告信息
  * 正则方式提取无法识别%类型的数值
* 示例代码：
```python
from ricco import to_float

to_float('10%')
# 0.1
to_float('10--', rex=1, rex_warning=0)
# 10.0
```
* func: `serise_to_float(serise)`
  * pandas.Series: str --> float
---
### 文件转换工具
* func: `csv2shp`
  * csv文件转shapefile，必须要有geometry字段
  * 由于列名为中文转换失败的会转化为汉语拼音去转换
* func: `shp2csv`
  * shapefile转csv
---
### 坐标转换工具
* func: `BD2WGS`
  * bd09（百度） --> wgs84，经纬度必须为lng和lat
* func: `GD2WGS`
  * gcj02（高德） --> wgs84，经纬度必须为lng和lat
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









