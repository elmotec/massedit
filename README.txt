Python Mass Editor
==================

Implements a python mass editor class to process multiple files using Python
code. The modification(s) is (are) shown on stdout as a diff output. One
can then modify the target file(s) in place with the -w/--write option.

.. ATTENTION::

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

  usage: massedit.py [-h] [-v] [-w] [-V] [-e EXPRESSIONS] [-s STARTDIR]
                     [-m MAXDEPTH] [-o output]
                     pattern [pattern ...]

  Python mass editor
  
  positional arguments:
    pattern               file patterns to process.

  optional arguments:
    -h, --help            show this help message and exit
    -v, --version         show program's version number and exit
    -w, --write           modify target file(s) in place. Shows diff otherwise.
    -V, --verbose         increases log verbosity (can be specified multiple
                          times)
    -e EXPRESSIONS, --expression EXPRESSIONS
                          Python expressions to be applied on all files. Use the
                          line variable to reference the current line.
    -s STARTDIR, --start STARTDIR
                          Starting directory in which to look for the files. If
                          there is one pattern only and it includes a directory,
                          the start dir will be that directory and the max depth
                          level will be set to 1.
    -m MAXDEPTH, --max-depth-level MAXDEPTH
                          Maximum depth when walking subdirectories.
    -o output, --output output
                          redirect output to a file
  
  example: massedit.py -e "re.sub('failIf', 'assertFalse', line)" *.py
  
    
or if massedit is installed as a package (from pypi for instance) :

::

  python -m massedit -e "re.sub('assertEquals', 'assertEqual', line)" test.py


There is also a convenient ``massedit.bat`` wrapper for Windows included in
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


History
-------

I have been using runsed and checksed (from Unix Power Tools) for years and
did not find a good substitute under Windows until I came across Graham 
Fawcett python recipe 437932_ on ActiveState. It inspired me to write the 
Python Mass Editor.

The core was fleshed up a little, and here we are. If you find it useful and
enhance it please, do not forget to submit patches. Thanks!

If you are more interested in awk-like tool, you probably will find pyp_ a
better alternative. This is certainly a more mature tool.


License
-------

Licensed under the term of `MIT License`_. See attached file LICENSE.txt.



.. _437932: http://code.activestate.com/recipes/437932-pyline-a-grep-like-sed-like-command-line-tool/
.. _Python re module: http://docs.python.org/library/re.html
.. _Pyp: http://code.google.com/p/pyp/
.. _MIT License: http://en.wikipedia.org/wiki/MIT_License
.. _autopep8: http://pypi.python.org/pypi/autopep8
.. _Ned Batchelder's article: http://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html

