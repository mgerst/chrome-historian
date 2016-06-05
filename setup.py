from setuptools import setup, find_packages

setup(
    name='chrome-historian',
    version='1.0',
    long_description=__doc__,
    packages=find_packages(),
    include_Package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask',
    ],
    entry_points={
        'console_scripts': ['chrome-historian=historian.historian:main'],
    },
)
