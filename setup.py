#!/usr/bin/env python

"""Packaging script."""

import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

setup(
    name="Python Mass Editor",
    version="0.52",
    author="Jerome Lecomte",
    author_email="jlecomte1972@yahoo.com",
    description='Edit multiple files using Python text processing modules',
    license="MIT",
    keywords="sed editor stream python edit",
    url="http://github.com/elmotec/massedit",
    packages=[],
    long_description=README + "\n\n" + CHANGES,
    test_suite='tests',
    setup_requires=[],
    tests_require=['mock'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development",
        "Topic :: Text Editors :: Text Processing",
        "Topic :: Utilities",
        "Intended Audience :: Developers",
    ],
)
