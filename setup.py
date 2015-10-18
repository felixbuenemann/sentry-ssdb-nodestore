#!/usr/bin/env python
"""
sentry-ssdb-nodestore
==============
An extension for Sentry which implements an SSDB NodeStorage backend
"""
from setuptools import setup

install_requires = [
    'ssdb.py>=0.1.8',
    'msgpack-python>=0.4.6',
    'sentry>=7.4.0',
]

tests_requires = [
]

setup(
    name='sentry-ssdb-nodestore',
    version='1.0.0',
    author='Felix Buenemann',
    author_email='felix.buenemann@gmail.com',
    url='http://github.com/felixbuenemann/sentry-ssdb-nodestore',
    description='A Sentry extension to add SSDB as a NodeStore backend.',
    long_description=__doc__,
    packages=['sentry_ssdb_nodestore'],
    license='BSD',
    zip_safe=False,
    install_requires=install_requires,
    tests_requires=tests_requires,
    test_suite='tests',
    include_package_data=True,
    download_url='https://pypi.python.org/pypi/sentry-ssdb-nodestore',
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
