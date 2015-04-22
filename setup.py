#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

os.system('make rst')
readme = open('README.rst').read()

setup(
    name='leicaexperiment',
    version=open(os.path.join('leicaexperiment', 'VERSION')).read().strip(),
    description='Read, stitch and compress Leica LAS Matrix Screener experiments',
    long_description=readme,
    author='Arve Seljebu',
    author_email='arve.seljebu@gmail.com',
    url='https://github.com/arve0/leicaexperiment',
    packages=[
        'leicaexperiment',
    ],
    package_dir={'leicaexperiment': 'leicaexperiment'},
    include_package_data=True,
    install_requires=[
        'pydebug',
        'Pillow',
        'fijibin',
        'lxml',
        'joblib'
    ],
    license='MIT',
    zip_safe=False,
    keywords='leicaexperiment',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
