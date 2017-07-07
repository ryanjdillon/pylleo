from setuptools import setup
from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pylleo',
    version='0.1',
    description=('Utilities for working with Little Leonardo datalogger '
          'data in Python'),
    long_description=long_description,
    author='Ryan J. Dillon',
    author_email='ryanjamesdillon@gmail.com',
    url='https://github.com/ryanjdillon/pylleo',
    download_url='https://github.com/ryanjdillon/pylleo/archive/0.1.tar.gz',
    license='GPL-3.0+',
    packages=['pylleo',],
    keywords=['datalogger','accelerometer'],
    classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Science/Research',
    'Programming Language :: Python :: 3.5'],
    zip_safe=False
    )
