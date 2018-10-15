#!/usr/bin/env python
from setuptools import setup


setup(name='xml2js',
      version='0.1',
      description='This package provides light-weighted xml to json conversion. '
                  'The conversion standard is from JavaScript package xml-js: https://github.com/nashwaan/xml-js.',
      author='Yang Zhengzhi',
      author_email='yangzhengzhi.roy@gmail.com',
      py_modules=['xml2js'],
      platforms=['all'],
      python_requires='>=3.5',
      install_requires=['lxml>=4.2.0'],
      classifiers=[
          'Intended Users: Developers',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
      ]
      )
