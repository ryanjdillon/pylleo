from setuptools import setup
import os

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pylleo',
    version='0.4',
    description=('Utilities for working with Little Leonardo datalogger '
          'data in Python'),
    long_description=long_description,
    author='Ryan J. Dillon',
    author_email='ryanjamesdillon@gmail.com',
    url='https://github.com/ryanjdillon/pylleo',
    download_url='https://github.com/ryanjdillon/pylleo/archive/0.4.tar.gz',
    license='GPL-3.0+',
    packages=['pylleo'],
    install_requires=[
        'bokeh==0.12.6',
        'click==6.7',
        'pandas==0.20.3',
        'yamlord==0.4'],
    scripts=['bin/pylleo-cal'],
    include_package_data=True,
    keywords=['datalogger','accelerometer','biotelemetry'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3.5'],
    zip_safe=False,
    )
