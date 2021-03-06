from setuptools import setup, find_packages
import os


def requirements(fp: str):
    with open(fp) as f:
        return [r.strip() for r in f.readlines()]


fp_readme = os.path.join(os.path.abspath(os.path.dirname(__file__)), "README.rst")
with open(fp_readme, encoding="utf-8") as f:
    long_description = f.read()

setup_requirements = ["pytest-runner", "setuptools_scm"]

setup(
    name="pylleo",
    description=(
        "Utilities for working with Little Leonardo datalogger " "data in Python"
    ),
    long_description=long_description,
    author="Ryan J. Dillon",
    author_email="ryanjamesdillon@gmail.com",
    url="https://github.com/ryanjdillon/pylleo",
    license="GPL-3.0+",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    setup_requires=setup_requirements,
    install_requires=requirements("requirements.in"),
    test_requires=requirements("requirements_test.txt"),
    scripts=["bin/pylleo-cal"],
    include_package_data=True,
    use_scm_version={"write_to": "src/pylleo/_version.py", "relative_to": __file__},
    keywords=["datalogger", "accelerometer", "biotelemetry"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.5",
    ],
    zip_safe=False,
)
