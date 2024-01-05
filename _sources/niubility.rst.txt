★★实用方法推荐★★
========================


数据读写
________________________


读取单个文件
^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: 自动识别文件类型并选择合适的方法读取，日常使用中99%以上的数据都可以用这一个方法读取

.. autofunction:: ricco.etl.extract.rdf
   :noindex:

.. code-block:: python

   from ricco import rdf
   df = rdf('/path/test.csv')


读取文件夹
^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: 自动识别文件类型并选择合适的方法读取整个文件夹的数据

.. autofunction:: ricco.etl.extract.rdf
   :noindex:

.. code-block:: python

   from ricco import rdf_by_dir
   df = rdf_by_dir('/path_dir/', exts=['.csv'])



保存文件
^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: 根据扩展名自动识别文件类型，并保存至对应的文件类型

.. autofunction:: ricco.etl.load.to_file
   :noindex:

.. code-block:: python

   import pandas as pd
   from ricco import to_file
   df = pd.DataFrame()
   to_file(df, '/path/test.csv')


文件处理
________________________


文件拆分
^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: 将文件拆分为多个文件，放置在与文件同名目录下；可按数据量和文件数量进行拆分；可自定义文件类型

.. autofunction:: ricco.etl.file.split2x
   :noindex:

.. code-block:: python

   from ricco import split2x
   split2x('/path/test.csv', chunksize=1000)
   split2x('/path/test.csv', parts=3)


文件批量处理reshape
^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: 将文件夹的文件大小进行统一拆分，并可传入自定义处理函数

.. autofunction:: ricco.etl.file.reshape_files
   :noindex:

.. code-block:: python

   from ricco import reshape_files

   def process(df):
     return df

   # 将'/path_dir/'中的文件，拆分为大小为1000的 csv 文件，并保存在'/path_dir_to/'目录下，
   # 处理过程中调用 'process' 方法进行处理
   reshape_files(
       from_dir='/path_dir/',
       to_dir='/path_dir_to/',
       to_ext='.csv',
       chunksize=1000,
       func=process,
   )


万能格式转换
^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: 批量转换可使用 `dir_file_to_x()`

.. autofunction:: ricco.etl.file.file_to_x
   :noindex:

.. code-block:: python

   from ricco import file_to_x
   # 将csv转为Excel文件，保存在相同目录下
   file_to_x('/path/test.csv', to_ext='.xlsx')


地理处理
________________________


自动转为shapely格式
^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: 将带有地理信息的数据，自动转为 shapely 格式的GeoDataframe，地理格式可以为wkb/wkt/geojson等

.. autofunction:: ricco.geometry.df.auto2shapely
   :noindex:

.. code-block:: python

   from ricco import auto2shapely
   from ricco import rdf

   df = rdf('./test.csv')
   auto2shapely(df)  # Return: GeoDataframe


shapely转为任意格式
^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: ricco.geometry.df.shapely2x
   :noindex:

.. code-block:: python

   from ricco import rdf
   from ricco import shapely2x

   df = rdf('./test.csv')
   # 转为wkb格式的Dataframe
   shapely2x(df, geometry_format='wkb')


shapely转为任意格式
^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: ricco.geometry.df.auto2x
   :noindex:

.. code-block:: python

   from ricco import rdf
   from ricco import auto2x

   df = rdf('./test.csv')
   # 转为wkb格式的Dataframe
   auto2x(df, geometry_format='wkb')



空间计算
________________________


投影变换
^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: 根据经纬度自动获取 epsg code 进行投影，也可以指定城市和 epsg code 进行投影，该方法是对geometry列进行投影；如需要对经纬度进行投影，请使用`projection_lnglat()`方法

.. autofunction:: ricco.geometry.df.projection
   :noindex:

.. autofunction:: ricco.geometry.df.projection_lnglat
   :noindex:


面积计算
^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: 自动地理转换、投影、计算面积，新增面积列`area`，不改变原数据

.. autofunction:: ricco.geometry.df.get_area
   :noindex:


近邻分析
^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: 计算一个数据集中的元素到另一个数据集中全部元素的最短距离（单位：米）,同时可进行其他统计

.. autofunction:: ricco.geometry.df.nearest_kdtree
   :noindex:

.. autofunction:: ricco.geometry.df.nearest_neighbor
   :noindex:


buffer计算
^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: 生成指定半径的buffer的geometry列

.. autofunction:: ricco.geometry.df.buffer
   :noindex:


空间统计
^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: 对面数据覆盖范围内的点数据进行空间统计

.. autofunction:: ricco.geometry.df.spatial_agg
   :noindex:


空间连接打标签
^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: ricco.geometry.df.mark_tags_v2
   :noindex:

.. code-block:: python

   from ricco import rdf
   from ricco import mark_tags_v2

   df_poi = rdf('./poi.csv')
   df_plate = rdf('./plate.csv')

   # 给POI数据打上plate_name的标签
   mark_tags_v2(df_poi, df_plate, col_list='plate_name')
