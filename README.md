# mdt_housing

用于存放地产组希望Share给其他组使用的代码，该项目将发布一个Pypi包


## 安装

要求python>=3.7

```bash
pip install -i https://pypi.idatatlas.com/deo/dev mdt_housing
```

## 使用

```python
from mdt_housing import hello

hello('world')
```

## 开发环境

推荐[virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/)创建虚拟环境

请先按官方文档安装vritualenvwrapper再执行下列操作

```bash
mkvirtualenv mdt_housing
pip install -r requirements.txt
pip install -r requirements_test.txt
```

## 测试

使用pytest框架写测试

- 如果不需要在Docker环境中跑测试，可以直接跑pytest

```bash
# 选本地安装mdt_housing
pip install -e .

# 运行测试
pytest test/

# 获取测试覆盖率
pytest --cov=. --cov-report html:cov_html test/
```

- 如果需要在Docker环境中跑测试，需要利用docker_compose_test.sh脚本

```bash
./docker_compose_test.sh -- pytest test/
```

## 发布


1. 更改版本号

使用[Sematic Version](https://semver.org/)管理版本号。
每次发布新包，都需要更改版本号，更改版本号使用[bump2version](https://github.com/c4urself/bump2version)软件。

```bash
bump2version patch
bump2version minor
bump2version major
```

2. 合并代码

更新版本号后，需要提前代码并合并到Master。

3. 创建Tag

创建一个Tag, Tag名称是版本号，比如v1.2.0。Gitlab CI会自动将数据打包发布到公司内部的pypi服务器。


## 代码规范

- 遵循Google Python代码规范：https://zh-google-styleguide.readthedocs.io/en/latest/google-python-styleguide/contents/

- 静态代码检查

推荐使用[pylint](https://www.pylint.org/)做静态代码检查，配置文件参考`.pylintrc`。
也可使用[flake8](https://flake8.pycqa.org/en/latest/), 配置文件参考`tox.ini`。

- import

import要求按字母排序，一行只import一个包。

可以借助[isort](https://github.com/timothycrosley/isort)对import自动规范化，配置文件参考`tox.ini`。

如果你偏好PyCharm作为IDE，可以直接导入该配置文件:
https://gitlab.idatatlas.com/mdt/wiki/-/tree/master/pycharm

- requirements.txt

按字母表排序
