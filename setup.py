#!/usr/bin/env python
# vim: set encoding=utf-8

"""Packaging script."""

import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

setup(
    name="massedit",
    version="0.64",
    author="Jérôme Lecomte",
    author_email="jlecomte1972@yahoo.com",
    description='Edit multiple files using Python text processing modules',
    license="MIT",
    keywords="sed editor stream python edit mass",
    url="http://github.com/elmotec/massedit",
    py_modules=['massedit'],
    entry_points={'console_scripts': ['massedit=massedit:main']},
    long_description=README,
    test_suite='tests',
    setup_requires=[],
    tests_require=['mock'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development",
        "Topic :: Text Editors :: Text Processing",
        "Topic :: Utilities",
        "Intended Audience :: Developers",
    ],
)
