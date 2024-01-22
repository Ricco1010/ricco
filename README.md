# 安装与更新

```shell
pip install ricco
pip install ricco -U # 或
pip install ricco --upgrade
```

# 文档

[Document](https://ricco1010.github.io/ricco/)

# 便捷方法介绍

## 数据读写

自动识别文件类型进行读写

1. 万能读取数据文件：`rdf()`

> * 支持`.xls/.xlsx/.csv/.parquet/.shp/.ovkml`等多种文件格式

```python
from ricco import rdf

df = rdf('/path/test.csv')
```

2. 读取文件夹中的数据：`rdf_by_dir()`

> * 适用于读取的文件夹中数据结构相同的多个数据，可指定扩展名，如不指定则读取所有文件；
> * 支持的文件格式与`rdf()`相同

```python
from ricco import rdf_by_dir

df = rdf_by_dir('/path_dir/', exts=['.csv'])
```

3. 文件保存：`to_file()`

> * 根据扩展名可自动报错多种格式的文件，支持的文件格式与`rdf()`相同
> * 可自动新建目录，避免了文件保存时需要手动创建目录的麻烦

```python
import pandas as pd
from ricco import to_file

df = pd.DataFrame()
to_file(df, '/path/test.csv')
```

## 文件处理

1. 文件拆分：`split2x()`

> * 将文件拆分为多个文件，放置在与文件同名目录下
> *
> * 支持的文件格式与`rdf()`相同，默认'.csv'

```python
from ricco import split2x

split2x('/path/test.csv', chunksize=1000)
split2x('/path/test.csv', parts=3)
```

2. 文件批量拆分：`reshape_files()`

> 将文件夹的文件大小进行统一拆分，并可传入自定义处理函数

```python
from ricco import reshape_files


def process(df):
  return df


# 将'/path_dir/'中的文件，拆分为大小为1000的 csv 文件，并保存在'/path_dir_to/'目录下，处理过程中调用 'process' 方法
reshape_files(
    from_dir='/path_dir/',
    to_dir='/path_dir_to/',
    to_ext='.csv',
    chunksize=1000,
    func=process,
)
```

3. 万能格式转换：`file_to_x()`

> 批量转换可使用`dir_file_to_x()`

```python
from ricco import file_to_x

# 将csv转为Excel文件，保存在相同目录下
file_to_x('/path/test.csv', to_ext='.xlsx')
```

## 地理处理

自动识别地理格式并进行转换，节省时间

1. 自动转为shapely格式：`auto2shapely()`

> 将带有地理信息的数据，自动转为 shapely 格式的GeoDataframe，地理格式可以为wkb/wkt/geojson等

```python
from ricco import auto2shapely
from ricco import rdf

df = rdf('./test.csv')
auto2shapely(df)  # Return: GeoDataframe
```

2. shapely转为任意格式：`shapely2x()`

```python
from ricco import rdf
from ricco import shapely2x

df = rdf('./test.csv')
# 转为wkb格式的Dataframe
shapely2x(df, geometry_format='wkb')  
```

3. 自动转为任务任意地理格式：`auto2x()`

```python
from ricco import rdf
from ricco import auto2x

df = rdf('./test.csv')
# 转为wkb格式的Dataframe
auto2x(df, geometry_format='wkb')
```

## 空间计算

1. 投影变换：`projection()`

> 根据经纬度自动获取 epsg code 进行投影，也可以指定城市和 epsg code 进行投影；
> 该方法是对geometry列进行投影，
> 如需要对经纬度进行投影，请使用`projection_lnglat()`方法

```python
from ricco.geometry.df import projection
```

2. 面积计算：`get_area()`

> 自动地理转换、投影、计算面积，新增面积列`area`，不改变原数据

```python
from ricco.geometry.df import get_area
```

3. 近邻分析：`nearest_kdtree()`和`nearest_neighbor()`

> 计算一个数据集中的元素到另一个数据集中全部元素的最短距离（单位：米）,
> 同时可进行其他统计

```python
from ricco.geometry.df import nearest_kdtree
from ricco.geometry.df import nearest_neighbor
```

4. buffer计算：`buffer()`

> 生成指定半径的buffer的geometry列

```python
from ricco.geometry.df import buffer
```

5. 空间统计：`spatial_agg()`

> 对面数据覆盖范围内的点数据进行空间统计

```python
from ricco.geometry.df import spatial_agg
```

6. 空间连接打标签：`mark_tags_v2()`

```python
from ricco import rdf
from ricco import mark_tags_v2

df_poi = rdf('./poi.csv')
df_plate = rdf('./plate.csv')

# 给POI数据打上plate_name的标签
mark_tags_v2(df_poi, df_plate, col_list='plate_name')

```

