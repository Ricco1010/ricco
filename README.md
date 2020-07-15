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
* `rdf()`
```python
from ricco import rdf
filename = 'data.csv'
df = rdf(filename)
```
> 文件格式目前支持`.csv/.xls/.xlsx/.shp`
* `split_csv(filename, n)`
```python
from ricco import split_csv
filename = 'data.csv'
split_csv(filename, n=2)
```
> 生成同名文件夹

> data
>> Part_0
>>
>>> data.csv
>>
>> Part_1
>>
>>> data.csv
* 文件要求
    * 其中输入文件为`.csv/.xls/.xlsx`，输出文件为`.csv` 
---
### dataframe及数据处理工具
* reset2name
* extract_num
* to_float
* serise_to_float

---
### 文件转换工具
* csv2shp
* shp2csv

---
### 坐标转换工具
* BD2WGS
* GD2WGS

---
### 空间计算工具
* valid_check
* circum_pio_num_geo_aoi
* mark_tags_df

---
### 其他工具
* mkdir_2
* pinyin










