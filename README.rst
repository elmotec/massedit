==================
Python Mass Editor
==================

Implements a python mass editor class to process multiple files using Python
code. The modification(s) is (are) shown on stdout as a diff output. One
can then modify the target file(s) in place with the -w/--write option.

Usage
-----

You probably will need to know the basics of the `Python re module`_ (regular expressions).

::

 usage: massedit.py [-h] [-c] [-v] [-e EXPRESSION] file [file ...]

 Python based mass file editor

 positional arguments:
   file                  file to process with the expression. Modified in
                         place.

 optional arguments:
   -h, --help            show this help message and exit
   -w, --write           modify the target files in place
   -v, --version         shows version number
   -V, --verbose         Increases verbosity
   -e EXPRESSIONS, --expression EXPRESSIONS
                         Python expression to be applied on all files. Use the
                         line variable to reference the current line.
  
Where *expression* is to be applied to a variable arbitrarily call ``line``. For instance, 
``re.sub('assertEquals', 'assertEqual', line)`` will replace all instances of assertEquals 
with assertEqual.

::

 massedit.py -e "re.sub('assertEquals', 'assertEqual', line)" file_to_modify.txt


Installation
------------

Download massedit.py from http://github.com/elmotec/massedit or:

::
  
  pip install massedit



Plans
-----

I intend to add support for a file of expressions as an argument to allow
multiple modification at once.


I also would like to find a satisfactory way (ie. easy to use) to handle
multiline regex as the current version works on a line by line basis.

Add magic variables ``lineno`` and ``filename`` in addition to ``line``.

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

Licensed under the term of `MIT License`_. See file LICENSE.



.. _437932: http://code.activestate.com/recipes/437932-pyline-a-grep-like-sed-like-command-line-tool/
.. _Python re module: http://docs.python.org/library/re.html
.. _Pyp: http://code.google.com/p/pyp/
.. _MIT License: http://en.wikipedia.org/wiki/MIT_License

