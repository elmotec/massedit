#!/usr/bin/env python

"""
Implements a python bulk editor class to apply the same code to many files.

See README.rst for more information.
"""


# Copyright (c) 2012 Jerome Lecomte
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
# THE SOFTWARE.


__version__ = '0.51'  # Update setup.py when changing version.


import os
import sys
import logging
import argparse
import difflib
import types
# Most manip will involve re so we include it here for convenience.
import re  # pylint: disable=W0611
import glob


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.WARNING)


class EditorError(RuntimeError):
    """Error raised by the Editor class."""
    pass


class Editor(object):
    """Processes input file or input line.

    Named arguments:
    code -- code expression to process the input with.
    """

    def __init__(self, **kwds):
        self.code_objs = []
        self._codes = []
        self.dry_run = None
        if 'module' in kwds:
            self.import_module(kwds['module'])
        if 'code' in kwds:
            self.append_code_expr(kwds['code'])
        if 'dry_run' in kwds:
            self.dry_run = kwds['dry_run']

    def edit_line_with_code(self, line, code_obj):
        """Edit a line with one code object built in the ctor."""
        try:
            result = eval(code_obj, globals(), locals())
        except TypeError as ex:
            raise EditorError("failed to execute {}: {}".format(
                self._codes, ex))
        if not result:
            raise EditorError(
                    "cannot process line '{}' with {}".format(
                    line, code_obj))
        elif isinstance(result, list) or isinstance(result, tuple):
            line = ' '.join([str(res_element) for res_element in result])
        else:
            line = str(result)
        return line

    def edit_line(self, line):
        """Edits a single line using the code expression."""
        for code_obj in self.code_objs:
            line = self.edit_line_with_code(line, code_obj)
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
            bak_file_name = file_name + ".bak"
            if os.path.exists(bak_file_name):
                raise EditorError("{} already exists".format(bak_file_name))
            try:
                os.rename(file_name, bak_file_name)
                open(file_name, "w").writelines(to_lines)
                os.unlink(bak_file_name)
            except:
                os.rename(bak_file_name, file_name)
                raise
        return list(diffs)

    def append_code_expr(self, code):
        """Compiles argument and adds it to the list of code objects."""
        assert(isinstance(code, types.StringTypes))  # expect a string.
        logger.debug("compiling code {}...".format(code))
        try:
            code_obj = compile(code, '<string>', 'eval')
            self.code_objs.append(code_obj)
            self._codes.append(code)
        except SyntaxError as syntax_err:
            logger.error("cannot compile {0}: {1}".format(
                code, syntax_err))
            raise
        logger.debug("compiled code {}".format(code))

    def set_code_expr(self, codes):
        """Convenience: sets all the code expressions at once."""
        self.code_objs = []
        self._codes = []
        for code in codes:
            self.append_code_expr(code)

    def import_module(self, module):  # pylint: disable=R0201
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
    assert(isinstance(verbose_count, int))
    if verbose_count < 0:
        verbose_count = 0
    if verbose_count > 4:
        verbose_count = 4
    levels = [logging.ERROR, logging.WARNING,
            logging.INFO, logging.DEBUG]
    return levels[verbose_count]


def setup_logger(verbose_count):
    """Sets up a logger object for this script."""
    logging.basicConfig(stream=sys.stderr)
    verbosity = get_verbosity(verbose_count)
    if (verbosity > 0):
        logger.setLevel(verbosity)
        logger.info("logger level set to {}".format(verbosity))


def expand_wildcards(files):
    """Expands wildcards in argument in case it is not done by the shell."""
    all_files = []
    for item in files:
        all_files += glob.glob(item)
    return all_files


def command_line(argv):
    """Main command line handler."""
    example = """
        example: {} -e "re.sub('failIf', 'assertFalse', line)" test*.py""".\
                format(os.path.basename(argv[0]))
    parser = argparse.ArgumentParser(
            description="Python based mass file editor",
            version=__version__,
            epilog=example)
    parser.add_argument("-w", "--write", dest="write",
            action="store_true", default=False,
            help="modify target file(s) in place")
    parser.add_argument("-V", "--verbose", dest="verbose_count",
            action="count", default=0,
            help="increases log verbosity (can be specified multiple times)")
    parser.add_argument('-e', "--expression", dest="expressions", nargs=1,
            help="Python expressions to be applied on all files. Use the line "
            "variable to reference the current line.")
    parser.add_argument('files', metavar="file", nargs='+',
            help="file to process with the expression. Modified in place.")
    arguments = parser.parse_args(argv[1:])
    setup_logger(int(arguments.verbose_count))
    dry_run = not arguments.write
    editor = Editor(dry_run=dry_run)
    if arguments.expressions:
        editor.set_code_expr(arguments.expressions)
    files = arguments.files
    if sys.platform == 'win32':
        files = expand_wildcards(files)
    for infile in files:
        diffs = editor.edit_file(infile)
        if dry_run:
            print("".join(diffs))
    return 1


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr)
    os_status = 1
    try:
        command_line(sys.argv)
        os_status = 0
    finally:
        logging.shutdown()
    sys.exit(os_status)
