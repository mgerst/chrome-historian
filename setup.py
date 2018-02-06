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
        'pytest-runner',
        'flake8',
    ],
    install_requires=[
        'Flask',
        'peewee==3.0.13',
        'terminaltables==3.1.0',
    ],
    tests_require=[
        'pytest',
        'pytest-sugar',
    ],
    extras_require={
        'docs': [
            'sphinx',
            'sphinx_rtd_theme',
        ]
    },
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
