#!/usr/bin/env python

import os
import sys
from pip.req import parse_requirements

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements('requirements.txt')

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
reqs = [str(ir.req) for ir in install_reqs]

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
    version='0.0.1',
    description='Read, stitch and compress Leica LAS MatrixS Screener experiments',
    long_description=readme,
    author='Arve Seljebu',
    author_email='arve.seljebu@gmail.com',
    url='https://github.com/arve0/leicaexperiment',
    packages=[
        'leicaexperiment',
    ],
    package_dir={'leicaexperiment': 'leicaexperiment'},
    include_package_data=True,
    install_requires=reqs,
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
