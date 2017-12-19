#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='chrome-historian',
    version='0.1',
    long_description=__doc__,
    packages=find_packages(),
    include_Package_data=True,
    zip_safe=False,

    setup_requires=[
        'flake8',
    ],
    install_requires=[
        'Flask',
        'peewee==2.10.2',
    ],
    entry_points={
        'console_scripts': ['chrome-historian=historian.historian:main'],
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
    ],
)