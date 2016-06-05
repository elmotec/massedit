#!/usr/bin/env python
# encoding: utf-8

"""Packaging script."""

import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
readme = open(os.path.join(here, 'README.rst')).read()

setup(
    name="massedit",
    version="0.68",
    author="Jérôme Lecomte",
    author_email="jlecomte1972@yahoo.com",
    description='Edit multiple files using Python text processing modules',
    license="MIT",
    keywords="sed editor stream python edit mass",
    url="http://github.com/elmotec/massedit",
    py_modules=['massedit'],
    entry_points={'console_scripts': ['massedit=massedit:main']},
    long_description=readme,
    test_suite='tests',
    setup_requires=[],
    tests_require=['mock'],
    classifiers=["Development Status :: 5 - Production/Stable",
                 "License :: OSI Approved :: MIT License",
                 "Environment :: Console",
                 "Natural Language :: English",
                 "Programming Language :: Python :: 2.7",
                 "Programming Language :: Python :: 3.3",
                 "Programming Language :: Python :: 3.4",
                 "Topic :: Software Development",
                 "Topic :: Software Development :: Code Generators",
                 "Topic :: Text Editors :: Text Processing",
                 "Topic :: Text Processing :: Filters",
                 "Topic :: Utilities",
                 "Intended Audience :: Developers",
                ],
)
