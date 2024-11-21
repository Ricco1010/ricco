安装
==========

* Python: >=3.9

.. code-block:: bash

   pip install ricco

安装步骤
------------------------

1. 创建并切换至虚拟环境（以conda为例）

.. code-block:: bash

   # 创建虚拟环境（以etl为例）
   conda create -n etl python=3.9
   # 激活虚拟环境
   conda activate etl

2. 安装geopandas

.. code-block:: bash

   # 安装geopandas之前建议先手动安装shapely，否则会安装shapely2
   pip install shapely==1.8.5.post1
   pip install geopandas==0.11.1

3. 安装ricco

.. code-block:: bash

   pip install ricco


在jupyter中切换虚拟环境
------------------------

Kernel -- Change Kernel

.. code-block:: bash

   # 激活虚拟环境
   conda activate etl

   # 安装ipykernel
   pip install ipykernel
   # 运行上述命令后可能已经可以进行虚拟环境切换了，如果不行的话，执行下面的命令

   # 将虚拟环境添加到jupyter
   python -m ipykernel install --user --name etl
   # 或（给kernel命名）
   python -m ipykernel install --user --name etl --display-name "Python (etl)"

   # 移除Kernel
   jupyter kernelspec list
   jupyter kernelspec uninstall etl
