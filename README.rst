========
MassEdit
========

Implements a python mass editor class to process multiple files at once.

Usage
-----

You will probably need to know the basics of the `Python re module`_ (regular expressions). The usage is:

::

 massedit.py [options] <expression> <file> [ <file> ... ]

Where *expression* is to be applied to a variable arbitrarily call line. For instance, re.sub('Duck', 'Donkey', line) will replace all instances of Duck with Donkey.

::

 massedit.py "re.sub('Duck', 'Donkey', line)" source.txt

History
-------

I have been using runsed and checksed (from Unix Power Tools) for years and
did not find a good substitute under Windows until I came across Graham 
Fawcett python recipe 437932_ on ActiveState. It inspired me to write 
massedit.


The core was fleshed up a little, and here we are. If you find it useful and
enhance it please, do not forget to submit patches. Thanks! 

.. _437932: http://code.activestate.com/recipes/437932-pyline-a-grep-like-sed-like-command-line-tool/
.. _Python re module: http://docs.python.org/library/re.html

