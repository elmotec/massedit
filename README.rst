========
massedit 
========

------------------------------------
formerly known as Python Mass Editor
------------------------------------

Implements a python mass editor class to process multiple files using Python
code. The modification(s) is (are) shown on stdout as a diff output. One
can then modify the target file(s) in place with the -w/--write option.

.. image:: https://travis-ci.org/elmotec/massedit.png?branch=master
    :target: https://travis-ci.org/elmotec/massedit
    :alt: Build Status

.. WARNING::

  This tool is usefull as far as it goes but it does rely on the python 
  ``eval()`` function and does not check the code being executed. 
  It is a major security risk and one should not use this tool
  in a production environment.

  See `Ned Batchelder's article`_ for a thorough discussion of the dangers 
  linked to ``eval()`` and ways to circumvent them. Note that None of the 
  counter-measure suggested in the article are implemented at this time.


Usage
-----

You probably will need to know the basics of the `Python re module`_ (regular 
expressions).

::
  
  usage: massedit.py [-h] [-v] [-w] [-V] [-e EXPRESSIONS] [-s START_DIR]
                     [-m MAX_DEPTH] [-o output]
                     pattern [pattern ...]
  
  Python mass editor
  
  positional arguments:
    pattern               shell-like file name patterns to process.
  
  optional arguments:
    -h, --help            show this help message and exit
    -v, --version         show program's version number and exit
    -w, --write           modify target file(s) in place. Shows diff otherwise.
    -V, --verbose         increases log verbosity (can be specified multiple
                          times)
    -e EXPRESSIONS, --expression EXPRESSIONS
                          Python expressions applied to target files. Use the
                          line variable to reference the current line.
    -f FUNCTIONS, --function FUNCTIONS
                          Python function to apply to target file. Takes file
                          content as input and yield lines. Specify function as
                          <module>:<function name>.                          
    -s START_DIR, --start START_DIR
                          Directory from which to look for target files.
    -m MAX_DEPTH, --max-depth-level MAX_DEPTH
                          Maximum depth when walking subdirectories.
    -o output, --output output
                          redirect output to a file
  
  Examples:
  # Simple string substitution (-e). Will show a diff. No changes applied.
  massedit.py -e "re.sub('failIf', 'assertFalse', line)" *.py
  
  # File level modifications (-f). Overwrites the files in place (-w).
  massedit.py -w -f fixer:main *.py
  
  # Will change all test*.py in subdirectories of tests.
  massedit.py -e "re.sub('failIf', 'assertFalse', line)" -s tests test*.py
  
    
If massedit is installed as a package (from pypi for instance), one can 
interact with it as a command line tool :

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
  
  pip install massedit


Plans
-----

- Add support for 3rd party tool (e.g. `autopep8`_) to process the files.
- Add support for a file of expressions as an argument to allow multiple 
  modification at once.
- Find a satisfactory way (ie. easy to use) to handle multiline regex as the 
  current version works on a line by line basis.
- Add magic variables ``lineno`` and ``filename`` in addition to ``line``.


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
better alternative. This is certainly a more mature tool.


License
-------

Licensed under the term of `MIT License`_. See attached file LICENSE.txt.


Changes
-------

0.65 (????-??-??)
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

Steven Myint, https://github.com/myint



.. _437932: http://code.activestate.com/recipes/437932-pyline-a-grep-like-sed-like-command-line-tool/
.. _Python re module: http://docs.python.org/library/re.html
.. _Pyp: http://code.google.com/p/pyp/
.. _MIT License: http://en.wikipedia.org/wiki/MIT_License
.. _autopep8: http://pypi.python.org/pypi/autopep8
.. _Ned Batchelder's article: http://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html

