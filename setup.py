#!/usr/bin/env python
# encoding: utf-8

# readme
import os
if os.path.exists('README.rst'):
    long_description = open('README.rst').read()
else:
    long_description = ''

from setuptools import setup, find_packages

setup(name='LeicaExperiment',
      version='0.1.0',
      description='This project have been renamed to MatrixScreener',
      author='Arve Seljebu',
      author_email='arve.seljebu@gmail.com',
      license='MIT',
      url='https://github.com/arve0/leicaexperiment',
      py_modules=['leicaexperiment'],
      install_requires=['tifffile', 'numpy'],
      long_description=long_description)
