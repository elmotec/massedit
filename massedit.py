#!/usr/bin/env python

__version__ = '$Revision$'

"""Implements a python stream editor class to process lines or files. 

I have been using runsed and checksed (from Unix Power Tools) for years and
did not find a good substitute under Windows until I came accross Graham 
Fawcett python recipe on :
http://code.activestate.com/recipes/437932-pyline-a-grep-like-sed-like-command-line-tool/

The core was fleshed up a little, and here we are. If you find it usefull and
enhance it please, do not forget to submit patches. Thanks! 
"""

import logging
import argparse
import difflib
import re  # Not really needed but most manip will involve re.


class EditorError(RuntimeError):
    """Error raised by the Editor class."""
    pass


class Editor(object):
    """Processes input file or input line.
    
    Named arguments:
    code -- code expression to process the input with. 
    """

    def __init__(self, **kwds):
        self.code_obj = None
        self.code = None
        if 'module' in kwds:
            self.set_module(kwds['module'])
        if 'code' in kwds:
            self.set_code_expr(kwds['code'])

    def edit_line(self, line):
        """Edits a single line using the code expression."""
        if self.code_obj:
            try:
                result = eval(self.code_obj, globals(), locals())
            except TypeError as ex:
                raise EditorError("failed to execute %s: %s" % (self.code, ex)) 
            if result is None or result is False:
                raise EditorError(
                        "cannot process line '%s' with %s" % 
                        (line, self.code))
            elif isinstance(result, list) or isinstance(result, tuple):
                line = ' '.join(map(str, result))
            else:
                line = str(result)
        return line

    def edit_file(self, file_name, dry_run=False):
        """Edit file in place, returns a list of modifications (unified diff).

        Arguments:
        file_name -- The name of the file.
        dry_run -- only return differences, but do not edit the file.
        """
        diffs = []
        from_lines = open(file_name).readlines()
        to_lines = [ self.edit_line(line) for line in from_lines ]
        diffs = difflib.unified_diff(from_lines, to_lines, 
                    fromfile=file_name, tofile='<new>')
        return list(diffs)

    def set_code_expr(self, code):
        """Compiles the code passed as argument."""
        file_name = '<string>'
        self.code = code
        self.code_obj = compile(self.code, file_name, 'eval')

    def set_module(self, module):
        """Imports module that are needed for the code expr to compile.
       
        Argument:
        module -- can be scalar string or a list of strings.
        """
        if isinstance(module, list):
            all_modules = module
        else:
            all_modules = [module]
        for mod in all_modules:
            globals()[mod] = __import__(mod.strip())
            

def get_verbosity(verbose_count):
    """Helper to convert a count of verbosity level to a logging level."""
    if verbose_count < 0:  verbose_count = 0   # pylint: disable=C0321
    if verbose_count > 4:  verbose_count = 4   # pylint: disable=C0321
    levels = [ logging.FATAL, logging.ERROR, logging.WARNING, 
            logging.INFO, logging.DEBUG ]
    return levels[verbose_count]


def main(args):
    """Main command line handler."""
    parser = argparse.ArgumentParser(description=
            "Regex-based file editor")
    parser.add_argument("-i", "--in-place", dest="inplace",
            action="store_true", default=False,
            help="in-place substitution")
    parser.add_argument("-c", "--check", dest="check",
            action="store_true", default=False,
            help="only show edit that are to take place")
    parser.add_argument("-v", "--verbose", dest="verbose_count",
            action="count", defaule="0", help="Increases verbosity")
    args = parser.parse_args()
    verbosity = get_verbosity(args.verbose_count)
    logging.getLogger().setLevel( verbosity )
    for infile in args:
        with open( infile, "r" ) as source:
            #process_file( source, args )
            pass
    return 1


if __name__ == "__main__":
    import sys
    logging.basicConfig( stream=sys.stderr )
    os_status = 1
    try:
        main(sys.argv)
        os_status = 0
    finally:
        logging.shutdown()
    sys.exit( os_status )

