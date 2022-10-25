#!/usr/bin/env python

from setuptools import find_packages, setup

with open("README.rst") as f:
    README = f.read()

setup(
    name="annotate_cerebellum",
    author="Dimitri RODARIE",
    description="Library containing tools to visualize and correct annotations of the cerebellum",
    long_description=README,
    long_description_content_type="text/",
    url="https://github.com/dbbs-lab/annotateCerebellum.git",
    download_url="https://github.com/dbbs-lab/annotateCerebellum.git",
    python_requires=">=3.7.0",
    install_requires=[
        "numpy>=1.15.0",
        "Pillow>=9.2.0",
    ],
    packages=find_packages(),
    include_package_data=True,
    setup_requires=[
        "setuptools_scm",
        'Sphinx>=1.3.6',
        'sphinx-rtd-theme>=0.1.9',
        'pynrrd>=0.4.3'
    ],
)
