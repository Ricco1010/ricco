# coding: utf-8

import os
import re

from setuptools import find_packages
from setuptools import setup

pwd = os.path.dirname(__file__)

with open(os.path.join(pwd, 'src', 'ricco', '__init__.py')) as f:
    VERSION = (
        re.compile(r""".*__version__ = ["'](.*?)['"]""", re.S)
            .match(f.read())
            .group(1)
    )

with open(os.path.join(pwd, 'README.md'), encoding='utf-8') as f:
    README = f.read()

setup(name='ricco',
      version=VERSION,
      description='tools',
      long_description=README,
      long_description_content_type="text/markdown",
      author="Ricco Wang",
      author_email="wyk_0610@163.com",
      packages=find_packages('src'),
      package_dir={'': 'src'},
      platforms='any',
      install_requires=['numpy>=0.17',
                        'pandas>=0.24',
                        'geojson>=2.5.0',
                        'pypinyin>=0.35.0',
                        'tqdm>=4.47.0',
                        'xlrd>=1.2.0'],
      classifiers=['Development Status :: 3 - Alpha',
                   'Intended Audience :: Developers',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 3',
                   'Topic :: Software Development :: Libraries'],
      url='https://github.com/Ricco1010/ricco')
