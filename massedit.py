#!/usr/bin/env python

"""Implements a python stream editor class to process lines or files.

I have been using runsed and checksed (from Unix Power Tools) for years and
did not find a good substitute under Windows until I came accross Graham
Fawcett python recipe on :
http://code.activestate.com/recipes/\
        437932-pyline-a-grep-like-sed-like-command-line-tool/

The core was fleshed up a little, and here we are. If you find it usefull and
enhance it please, do not forget to submit patches. Thanks!

Licensed under the term of MIT License. See file LICENSE.
"""

__version__ = '$Revision$'

import os
import logging
import argparse
import difflib
# Most manip will involve re so we include it here for convenience.
import re  # pylint: disable=W0611


logger = logging.getLogger(__name__)


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
        self._code = None
        self.dry_run = None
        if 'module' in kwds:
            self.set_module(kwds['module'])
        if 'code' in kwds:
            self.set_code_expr(kwds['code'])
        if 'dry_run' in kwds:
            self.dry_run = kwds['dry_run']

    def edit_line(self, line):
        """Edits a single line using the code expression."""
        if self.code_obj:
            try:
                result = eval(self.code_obj, globals(), locals())
            except TypeError as ex:
                raise EditorError("failed to execute %{0}: %{1}".format(
                    self._code, ex))
            if not result:
                raise EditorError(
                        "cannot process line '%s' with %s" %
                        (line, self._code))
            elif isinstance(result, list) or isinstance(result, tuple):
                line = ' '.join([str(res_element) for res_element in result])
            else:
                line = str(result)
        return line

    def edit_file(self, file_name):
        """Edit file in place, returns a list of modifications (unified diff).

        Arguments:
        file_name -- The name of the file.
        dry_run -- only return differences, but do not edit the file.
        """
        diffs = []
        from_lines = open(file_name).readlines()
        to_lines = [self.edit_line(line) for line in from_lines]
        diffs = difflib.unified_diff(from_lines, to_lines,
                    fromfile=file_name, tofile='<new>')
        if not self.dry_run:
            replace_file_name = file_name + ".new"
            if os.path.exists(replace_file_name):
                raise EditorError("%s already exists" % replace_file_name)
            open(replace_file_name, "w").writelines(to_lines)
            os.unlink(file_name)
            os.rename(replace_file_name, file_name)
        return list(diffs)

    def set_code_expr(self, code):
        """Compiles the code passed as argument."""
        file_name = '<string>'
        self._code = code
        try:
            self.code_obj = compile(self._code, file_name, 'eval')
        except SyntaxError as error:
            logger.error("cannot compile {0}: {1}".format(self._code, error))
            self.code_obj = None
            raise

    def set_module(self, module):  # pylint: disable=R0201
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
    if verbose_count < 0:
        verbose_count = 0
    if verbose_count > 4:
        verbose_count = 4
    levels = [logging.FATAL, logging.ERROR, logging.WARNING,
            logging.INFO, logging.DEBUG]
    return levels[verbose_count]


def setup_logger(verbose_count):
    """Sets up a logger object for this script."""
    verbosity = get_verbosity(verbose_count)
    console = logging.StreamHandler()
    console.setLevel(verbosity)
    logger.addHandler(console)
    return logger


def command_line(argv):
    """Main command line handler."""
    parser = argparse.ArgumentParser(description="Python based file editor")
    parser.add_argument("-c", "--check", dest="check",
            action="store_true", default=False,
            help="only show edit that are to take place")
    parser.add_argument("-v", "--verbose", dest="verbose_count",
            action="count", default="0", help="Increases verbosity")
    parser.add_argument('-e', "--expression", dest="expression",
            help="Python expression to be applied on all files. Use the line "
            "variable to reference the current line.")
    parser.add_argument('files', metavar="file", nargs='+',
            help="file to process with the expression. Modified in place.")
    arguments = parser.parse_args(argv)
    setup_logger(arguments.verbose_count)
    editor = Editor(dry_run=arguments.check)
    if arguments.expression:
        editor.set_code_expr(arguments.expression)
    for infile in arguments.files:
        editor.edit_file(infile)
    return 1


if __name__ == "__main__":
    import sys
    logging.basicConfig(stream=sys.stderr)
    os_status = 1
    try:
        command_line(sys.argv)
        os_status = 0
    finally:
        logging.shutdown()
    sys.exit(os_status)
