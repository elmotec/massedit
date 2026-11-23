.. image:: https://img.shields.io/pypi/v/massedit.svg
    :target: https://pypi.python.org/pypi/massedit/
    :alt: PyPi version

.. image:: https://img.shields.io/pypi/pyversions/massedit.svg
    :target: https://pypi.python.org/pypi/massedit/
    :alt: Python compatibility

.. image:: https://img.shields.io/github/actions/workflow/status/elmotec/massedit/python-app.yml
   :target: https://github.com/elmotec/massedit/actions/workflows/python-app.yml
   :alt: GitHub Actions Workflow Status

.. image:: https://img.shields.io/pypi/dm/massedit.svg
    :alt: PyPi
    :target: https://pypi.python.org/pypi/massedit

.. image:: https://img.shields.io/librariesio/release/pypi/massedit.svg?label=libraries.io
    :alt: Libraries.io dependency status for latest release
    :target: https://libraries.io/pypi/massedit


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
                            from stdin. If none of --expression, --function or
                            --executable is given, the first argument is used as
                            one of them, guessing which it is.

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

    # Without -e, -f or -x, the first argument is guessed to be an
    # expression, a function or an executable (here an expression).
    massedit.py "re.sub('failIf', 'assertFalse', line)" *.py

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

Python 3.11 or later is required. Use Python 3.15 for development.

To set things up for development, use the steps below to install massedit in
editable mode and the development tools, including Commitizen for conventional
commits, and set up the pre-commit Git hook.

On Linux and macOS, run::

    make install

On Windows, run these commands in PowerShell::

    uv sync
    uv run --no-sync pre-commit install


License
-------

Licensed under the term of `MIT License`_. See attached file LICENSE.txt.


See the `changelog <https://github.com/elmotec/massedit/blob/main/CHANGELOG.md>`_
for release history.


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
