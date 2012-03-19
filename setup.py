import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "Python Mass Editor",
    version = "0.1",
    author = "Jerome Lecomte",
    author_email = "jlecomte1972@yahoo.com",
    description = ("."),
    license = "MIT",
    keywords = "sed editor stream python edit",
    url = "http://packages.python.org/massedit",
    packages=[],
    long_description=read('README.rst'),
    test_suite='tests',
    setup_requires=[],
    tests_require=[],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development",
        "Topic :: Text Editors :: Text Processing",
        "Topic :: Utilites",
        "Intended Audience :: Developers",
    ],
)

