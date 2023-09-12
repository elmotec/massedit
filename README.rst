.. image:: https://img.shields.io/pypi/v/massedit.svg
    :target: https://pypi.python.org/pypi/massedit/
    :alt: PyPi version

.. image:: https://img.shields.io/pypi/pyversions/massedit.svg
    :target: https://pypi.python.org/pypi/massedit/
    :alt: Python compatibility

.. image:: https://img.shields.io/github/workflow/status/elmotec/massedit/Python%20application
    :target: https://github.com/elmotec/massedit/actions?query=workflow%3A%22Python+application%22
    :alt: GitHub Workflow Python application

.. image:: https://img.shields.io/appveyor/ci/elmotec/massedit.svg?label=AppVeyor
    :target: https://ci.appveyor.com/project/elmotec/massedit
    :alt: AppVeyor status

.. image:: https://img.shields.io/pypi/dm/massedit.svg
    :alt: PyPi
    :target: https://pypi.python.org/pypi/massedit

.. image:: https://img.shields.io/librariesio/release/pypi/massedit.svg?label=libraries.io
    :alt: Libraries.io dependency status for latest release
    :target: https://libraries.io/pypi/massedit

.. image:: https://coveralls.io/repos/elmotec/massedit/badge.svg
    :target: https://coveralls.io/r/elmotec/massedit
    :alt: Coverage

.. image:: https://img.shields.io/codacy/grade/474b0af6853a4c5f8f9214d3220571f9.svg
    :target: https://www.codacy.com/app/elmotec/massedit/dashboard
    :alt: Codacy


========
massedit
========

*formerly known as Python Mass Editor*

Implements a python mass editor to process text files using Python
code. The modification(s) is (are) shown on stdout as a diff output. One
can then modify the target file(s) in place with the -w/--write option.
This is very similar to 2to3 tool that ships with Python 3.


+--------------------------------------------------------------------------+
| **WARNING**: A word of caution about the usage of ``eval()``             |
+--------------------------------------------------------------------------+
| This tool is useful as far as it goes but it does rely on the python     |
| ``eval()`` function and does not check the code being executed.          |
| **It is a major security risk** and one should not use this tool in a    |
| production environment.                                                  |
|                                                                          |
| See `Ned Batchelder's article`_ for a thorough discussion of the dangers |
| linked to ``eval()`` and ways to circumvent them. Note that None of the  |
| counter-measure suggested in the article are implemented at this time.   |
+--------------------------------------------------------------------------+

Usage
-----

You probably will need to know the basics of the `Python re module`_ (regular
expressions).

::

    usage: massedit.py [-h] [-V] [-w] [-v] [-e EXPRESSIONS] [-f FUNCTIONS]
                       [-x EXECUTABLES] [-s START_DIRS] [-m MAX_DEPTH] [-o FILE]
                       [-g FILE] [--encoding ENCODING] [--newline NEWLINE]
                       [file pattern [file pattern ...]]

    Python mass editor

    positional arguments:
      file pattern          shell-like file name patterns to process or - to read
                            from stdin.

    optional arguments:
      -h, --help            show this help message and exit
      -V, --version         show program's version number and exit
      -w, --write           modify target file(s) in place. Shows diff otherwise.
      -v, --verbose         increases log verbosity (can be specified multiple
                            times)
      -e EXPRESSIONS, --expression EXPRESSIONS
                            Python expressions applied to target files. Use the
                            line variable to reference the current line.
      -f FUNCTIONS, --function FUNCTIONS
                            Python function to apply to target file. Takes file
                            content as input and yield lines. Specify function as
                            [module]:?<function name>.
      -x EXECUTABLES, --executable EXECUTABLES
                            Python executable to apply to target file.
      -s START_DIRS, --start START_DIRS
                            Directory(ies) from which to look for targets.
      -m MAX_DEPTH, --max-depth-level MAX_DEPTH
                            Maximum depth when walking subdirectories.
      -o FILE, --output FILE
                            redirect output to a file
      -g FILE, --generate FILE
                            generate stub file suitable for -f option
      --encoding ENCODING   Encoding of input and output files
      --newline NEWLINE     Newline character for output files

    Examples:
    # Simple string substitution (-e). Will show a diff. No changes applied.
    massedit.py -e "re.sub('failIf', 'assertFalse', line)" *.py

    # File level modifications (-f). Overwrites the files in place (-w).
    massedit.py -w -f fixer:fixit *.py

    # Will change all test*.py in subdirectories of tests.
    massedit.py -e "re.sub('failIf', 'assertFalse', line)" -s tests test*.py

    # Will transform virtual methods (almost) to MOCK_METHOD suitable for gmock (see https://github.com/google/googletest).
    massedit.py -e "re.sub(r'\s*virtual\s+([\w:<>,\s&*]+)\s+(\w+)(\([^\)]*\))\s*((\w+)*)(=\s*0)?;', 'MOCK_METHOD(\g<1>, \g<2>, \g<3>, (\g<4>, override));', line)" gmock_test.cpp


If massedit is installed as a package (from pypi for instance), one can interact with it as a command line tool:

::

  python -m massedit -e "re.sub('assertEquals', 'assertEqual', line)" test.py


Or as a library (command line option above to be passed as kewyord arguments):

::

  >>> import massedit
  >>> filenames = ['massedit.py']
  >>> massedit.edit_files(filenames, ["re.sub('Jerome', 'J.', line)"])


Lastly, there is a convenient ``massedit.bat`` wrapper for Windows included in
the distribution.


Installation
------------

Download ``massedit.py`` from ``http://github.com/elmotec/massedit`` or :

::

  python -m pip install massedit


Poor man source-to-source manipulation
--------------------------------------

I find myself using massedit mostly for source to source modification of
large code bases like this:

First create a ``fixer.py`` python module with the function that will
process your source code. For instance, to add a header:

::

  def add_header(lines, file_name):
      yield '// This is my header'  # will be the first line of the file.
      for line in lines:
          yield line


Adds the location of ``fixer.py`` to your ``$PYTHONPATH``, then simply
call ``massedit.py`` like this:

::

  massedit.py -f fixer:add_header *.h


You can add the ``-s .`` option to process all the ``.h`` files reccursively.


Plans
-----

- Add support for 3rd party tool (e.g. `autopep8`_) to process the files.
- Add support for a file of expressions as an argument to allow multiple
  modification at once.
- Find a satisfactory way (ie. easy to use) to handle multiline regex as the
  current version works on a line by line basis.


Rationale
---------

- I have a hard time practicing more than a few dialects of regular
  expressions.
- I need something portable to Windows without being bothered by eol.
- I believe Python is the ideal tool to build something more powerful than
  simple regex based substitutions.


Background
----------

I have been using runsed and checksed (from Unix Power Tools) for years and
did not find a good substitute under Windows until I came across Graham
Fawcett python recipe 437932_ on ActiveState. It inspired me to write the
massedit.

The core was fleshed up a little, and here we are. If you find it useful and
enhance it please, do not forget to submit patches. Thanks!

If you are more interested in awk-like tool, you probably will find pyp_ a
better alternative.


Contributing
------------

To set things up for development, the easiest is to pip-install the develop
extra configuration:

::

    python -m venv venv
    . venv/bin/activate
    python -m pip install -e .[develop]


The best is to use commitizen_ when performing commits.

License
-------

Licensed under the term of `MIT License`_. See attached file LICENSE.txt.


Changes
-------

See CHANGELOG.md for changes later than 0.69.0

0.69.1 (2023-09-10)
  Updated infrastructure files to setup.cfg/pyproject.toml instead of
  setup.py.  Thanks @isidroas.

0.69.0 (2020-12-22)
  Also moved CI to github workflows from travis and added
  regression tests for Python 2.7.

0.68.6 (2019-12-02)
  Added support for Python 3.8, stdin input via - argument. Documented
  regex to turn base classes into googlemock MOCK_METHOD.

0.68.5 (2019-04-13)
  Added --newline option to force newline output. Thanks @ALFNeT!

0.68.4 (2017-10-24)
  Fixed bug that would cause changes to be missed when the -w option is
  ommited. Thanks @tgoodlet!

0.68.3 (2017-09-20)
  Added --generate option to quickly generate a fixer.py template file
  to be modified to be used with -f fixer.fixit option. Added official
  support for Python 3.6

0.68.1 (2016-06-04)
  Fixed encoding issues when processing non-ascii files.
  Added --encoding option to force the value of the encoding if need be.
  Listed support for Python 3.5

0.67.1 (2015-06-28)
  Documentation fixes.

0.67 (2015-06-23)
  Added file_name argument to processing functions.
  Fixed incorrect closing of sys.stdout/stderr.
  Improved diagnostic when the processing function does not take 2 arguments.
  Swapped -v and -V option to be consistent with Python.
  Pylint fixes.
  Added support for Python 3.4.
  Dropped support for Python 3.2.

0.66 (2013-07-14)
  Fixed lost executable bit with -f option (thanks myint).

0.65 (2013-07-12)
  Added -f option to execute code in a separate file/module. Added Travis continuous integration (thanks myint). Fixed python 2.7 support (thanks myint).

0.64 (2013-06-01)
  Fixed setup.py so that massedit installs as a script. Fixed eol issues (thanks myint).

0.63 (2013-05-27)
  Renamed to massedit. Previous version are still known as Python-Mass-Editor.

0.62 (2013-04-11)
  Fixed bug that caused an EditorError to be raised when the result of the
  expression is an empty string.

0.61 (2012-07-06)
  Added massedit.edit_files function to ease usage as library instead of as
  a command line tool (suggested by Maxim Veksler).

0.60 (2012-07-04)
  Treats arguments as patterns rather than files to ease processing of
  multiple files in multiple subdirectories.  Added -s (start directory)
  and -m (max depth) options.

0.52 (2012-06-05)
  Upgraded for python 3. Still compatible with python 2.7.

0.51 (2012-05)
  Initial release (Beta).


Contributor acknowledgement
---------------------------

https://github.com/myint
https://github.com/tgoodlet
https://github.com/ALFNeT
https://github.com/isidroas



.. _437932: http://code.activestate.com/recipes/437932-pyline-a-grep-like-sed-like-command-line-tool/
.. _Python re module: http://docs.python.org/library/re.html
.. _Pyp: http://code.google.com/p/pyp/
.. _MIT License: http://en.wikipedia.org/wiki/MIT_License
.. _autopep8: http://pypi.python.org/pypi/autopep8
.. _Ned Batchelder's article: http://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html
.. _commitizen: https://commitizen-tools.github.io/commitizen/
