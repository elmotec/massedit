#!/usr/bin/env python
# coding: utf-8

"""A python bulk editor class to apply the same code to many files."""

# Copyright (c) 2012, 2013 Jérôme Lecomte
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

from __future__ import unicode_literals


__version__ = '0.65'  # UPDATE setup.py when changing version.
__author__ = 'Jérôme Lecomte'
__license__ = 'MIT'


import sys

import os
import logging
import argparse
import difflib
# Most manip will involve re so we include it here for convenience.
import re  # pylint: disable=W0611
import fnmatch
import io
import subprocess


log = logging.getLogger(__name__)


try:
    unicode
except NameError:
    unicode = str


def get_function(function_name):
    """Retrieves the function defined by the function_name.

    Arguments:
      function_name: specification of the type module:function_name.
    """
    module_name, callable_name = function_name.split(':')
    current = globals()
    if not callable_name:
        callable_name = module_name
    else:
        import importlib
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            log.error("failed to import {}".format(module_name))
            raise
        current = module
    try:
        for level in callable_name.split('.'):
            current = getattr(current, level)
    except AttributeError as err:
        msg = "cannot find {} in {}: {}"
        log.error(msg.format(level, current.__name__, err))
        raise
    if not current:
        raise ValueError("cannot find {} in module {}".format(class_name,
                                                              module.__name__))
    return current


class MassEdit(object):
    """Processes input file or input line.

    Named arguments:
      code: code expression to process the input with.
    """

    def __init__(self, **kwds):
        self.code_objs = dict()
        self._codes = []
        self._functions = []
        self._executables = []
        self.dry_run = None
        if 'module' in kwds:
            self.import_module(kwds['module'])
        if 'code' in kwds:
            self.append_code_expr(kwds['code'])
        if 'function' in kwds:
            self.append_function(kwds['function'])
        if 'executable' in kwds:
            self.append_executable(kwds['executable'])
        if 'dry_run' in kwds:
            self.dry_run = kwds['dry_run']

    def __edit_line(self, line, code, code_obj):  # pylint: disable=R0201
        """Edit a line with one code object built in the ctor."""
        try:
            result = eval(code_obj, globals(), locals())
        except TypeError as ex:
            message = "failed to execute {}: {}".format(code, ex)
            log.error(message)
            raise
        if result is None:
            log.error("cannot process line '{}' with {}".format(line, code))
            raise
        elif isinstance(result, list) or isinstance(result, tuple):
            line = ' '.join([unicode(res_element) for res_element in result])
        else:
            line = unicode(result)
        return line

    def edit_line(self, line):
        """Edits a single line using the code expression."""
        for code, code_obj in self.code_objs.items():
            line = self.__edit_line(line, code, code_obj)
        return line

    def edit_content(self, lines):
        """Processes a file contents.

        First processes the contents line by line applying the registered
        expressions, then process the resulting contents using the registered
        functions.

        Arguments:
          lines: file content.
        """
        lines = [self.edit_line(line) for line in lines]
        for function in self._functions:
            try:
                lines = function(lines)
            except Exception as err:
                msg = "failed to execute code: {}".format(err)
                log.error(msg)
                raise  # Let the exception be handled at a higher level.
        return lines

    def edit_file(self, file_name):
        """Edit file in place, returns a list of modifications (unified diff).

        Arguments:
          file_name: The name of the file.
          dry_run: only return differences, but do not edit the file.
        """
        with io.open(file_name, "r", encoding='utf-8') as from_file:
            from_lines = from_file.readlines()

        if self._executables:
            nbExecutables = len(self._executables)
            if nbExecutables > 1:
                log.warn("found {} executables; only the first one is used".
                         format(nbExecutables))
            exec_list = self._executables[0].split()
            exec_list.append(file_name)
            try:
                log.info("running {}".format(" ".join(exec_list)))
                output = subprocess.check_output(exec_list,
                                                 universal_newlines=True)
            except Exception as err:
                msg = "failed to execute {}: {}"
                log.error(msg.format(" ".join(exec_list), err))
                raise  # Let the exception be handled at a higher level.
            to_lines = output.split("\n")
        else:
            to_lines = from_lines

        # unified_diff wants structure of known length. Convert to a list.
        to_lines = list(self.edit_content(to_lines))
        diffs = difflib.unified_diff(from_lines, to_lines,
                                     fromfile=file_name, tofile='<new>')
        if not self.dry_run:
            bak_file_name = file_name + ".bak"
            if os.path.exists(bak_file_name):
                msg = "{} already exists".format(bak_file_name)
                raise FileExistsError(msg)
            try:
                os.rename(file_name, bak_file_name)
                with io.open(file_name, "w", encoding='utf-8') as new_file:
                    new_file.writelines(to_lines)
            except Exception as err:
                msg = "failed to write output to {}: {}"
                log.error(msg.format(file_name, err))
                # Try to recover...
                try:
                    os.rename(bak_file_name, file_name)
                except Exception as err:
                    msg = "failed to restore {} from {}: {}"
                    log.error(msg.format(file_name, bak_file_name, err))
                raise
            try:
                os.unlink(bak_file_name)
            except Exception as err:
                msg = "failed to remove backup {}: {}"
                log.warning(msg.format(bak_file_name, err))
        return list(diffs)

    def append_code_expr(self, code):
        """Compiles argument and adds it to the list of code objects."""
        if not isinstance(code, str):  # expects a string.
            raise TypeError("string expected")
        log.debug("compiling code {}...".format(code))
        try:
            code_obj = compile(code, '<string>', 'eval')
            self.code_objs[code] = code_obj
        except SyntaxError as syntax_err:
            log.error("cannot compile {0}: {1}".format(
                code, syntax_err))
            raise
        log.debug("compiled code {}".format(code))

    def append_function(self, function):
        """Appends the function to the list of functions to be called.

        If the function is already a callable, use it. If it's a type str
        try to interpret it as [module]:?<callable>, load the module
        if there is one and retrieve the callable.

        Argument:
          function: a callable or the name of a callable.
        """
        if not hasattr(function, '__call__'):
            function = get_function(function)
            if not hasattr(function, '__call__'):
                raise ValueError("function is expected to be callable")
        self._functions.append(function)
        log.debug("registered {}".format(function.__name__))

    def append_executable(self, executable):
        """Appends an executable os command to the list to be called.

        Argument:
          executable: os callable executable.
        """
        if not isinstance(executable, str):
            raise TypeError("expected executable name as str, not {}".
                            format(executable.__class__.__name__))
        self._executables.append(executable)

    def set_code_exprs(self, codes):
        """Convenience: sets all the code expressions at once."""
        self.code_objs = dict()
        self._codes = []
        for code in codes:
            self.append_code_expr(code)

    def set_functions(self, functions):
        for function in functions:
            self.append_function(function)

    def set_executables(self, executables):
        for executable in executables:
            self.append_executable(executable)

    def import_module(self, module):  # pylint: disable=R0201
        """Imports module that are needed for the code expr to compile.

        Argument:
          module: can be scalar string or a list of strings.
        """
        if isinstance(module, list):
            all_modules = module
        else:
            all_modules = [module]
        for mod in all_modules:
            globals()[mod] = __import__(mod.strip())


def parse_command_line(argv):
    """Parses command line argument. See -h option

    Arguments:
      argv: arguments on the command line must include caller file name.
    """
    import textwrap

    example = textwrap.dedent("""
    Examples:
    # Simple string substitution (-e). Will show a diff. No changes applied.
    {0} -e "re.sub('failIf', 'assertFalse', line)" *.py

    # File level modifications (-f). Overwrites the files in place (-w).
    {0} -w -f fixer:main *.py

    # Will change all test*.py in subdirectories of tests.
    {0} -e "re.sub('failIf', 'assertFalse', line)" -s tests test*.py
    """).format(os.path.basename(argv[0]))
    formatter_class = argparse.RawDescriptionHelpFormatter
    if sys.version_info[0] < 3:
        parser = argparse.ArgumentParser(description="Python mass editor",
                                         version=__version__,
                                         epilog=example,
                                         formatter_class=formatter_class)
    else:
        parser = argparse.ArgumentParser(description="Python mass editor",
                                         epilog=example,
                                         formatter_class=formatter_class)
        parser.add_argument("-v", "--version", action="version",
                            version="%(prog)s {}".format(__version__))
    parser.add_argument("-w", "--write", dest="dry_run",
                        action="store_false", default=True,
                        help="modify target file(s) in place. "
                        "Shows diff otherwise.")
    parser.add_argument("-V", "--verbose", dest="verbose_count",
                        action="count", default=0,
                        help="increases log verbosity (can be specified "
                        "multiple times)")
    parser.add_argument('-e', "--expression", dest="expressions", nargs=1,
                        help="Python expressions applied to target files. "
                        "Use the line variable to reference the current line.")
    parser.add_argument('-f', "--function", dest="functions", nargs=1,
                        help="Python function to apply to target file. "
                        "Takes file content as input and yield lines. "
                        "Specify function as [module]:?<function name>.")
    parser.add_argument('-x', "--executable", dest="executables", nargs=1,
                        help="Python executable to apply to target file.")
    parser.add_argument("-s", "--start", dest="start_dir",
                        help="Directory from which to look for target files.")
    parser.add_argument('-m', "--max-depth-level", type=int, dest="max_depth",
                        help="Maximum depth when walking subdirectories.")
    parser.add_argument('-o', '--output', metavar="output",
                        type=argparse.FileType('w'), default=sys.stdout,
                        help="redirect output to a file")
    parser.add_argument('patterns', metavar="pattern",
                        nargs='+',  # argparse.REMAINDER,
                        help="shell-like file name patterns to process.")
    arguments = parser.parse_args(argv[1:])
    # Sets log level to WARN going more verbose for each new -V.
    log.setLevel(max(3 - arguments.verbose_count, 0) * 10)
    return arguments

def get_paths(patterns, start_dir=None, max_depth=1):
    """Retrieve files that match any of the patterns."""

    # Shortcut: if there is only one pattern, make sure we process just that.
    if len(patterns) == 1 and not start_dir:
        pattern = patterns[0]
        directory = os.path.dirname(pattern)
        if directory:
            patterns = [os.path.basename(pattern)]
            start_dir = directory
            max_depth = 1

    if not start_dir:
        start_dir = os.getcwd()
    for root, dirs, files in os.walk(start_dir):  # pylint: disable=W0612
        if max_depth is not None:
            relpath = os.path.relpath(root, start=start_dir)
            depth = len(relpath.split(os.sep))
            if depth > max_depth:
                continue
        names = []
        for pattern in patterns:
            names += fnmatch.filter(files, pattern)
        for name in names:
            path = os.path.join(root, name)
            yield path


def edit_files(patterns, expressions=[],  # pylint: disable=R0913, R0914
               functions=[], executables=[],
               start_dir=None, max_depth=1, dry_run=True,
               output=sys.stdout):
    """Process patterns with MassEdit.

    Arguments:
      patterns: file pattern to identify the files to be processed.
      expressions: single python expression to be applied line by line.
      functions: functions to process files contents.
      executables: os executables to execute on the argument files.

    Keyword arguments:
      max_depth: maximum recursion level when looking for file matches.
      start_dir: directory where to start the file search.
      dry_run: only display differences if True. Save modified file otherwise.
      output: handle where the output should be redirected.

    Returns:
      list of files processed.
    """
    # Makes for a better diagnostic because str are also iterable.
    if not iter(patterns) or isinstance(patterns, str):
        raise TypeError("patterns should be a list")
    if expressions and (not iter(expressions) or isinstance(expressions, str)):
        raise TypeError("expressions should be a list of exec expressions")
    if functions and (not iter(functions) or isinstance(functions, str)):
        raise TypeError("functions should be a list of functions")
    if executables and (not iter(executables) or isinstance(executables, str)):
        raise TypeError("executables should be a list of program names")

    editor = MassEdit(dry_run=dry_run)
    if expressions:
        editor.set_code_exprs(expressions)
    if functions:
        editor.set_functions(functions)
    if executables:
        editor.set_executables(executables)

    processed_paths = []
    for path in get_paths(patterns, start_dir=start_dir, max_depth=max_depth):
        diffs = list(editor.edit_file(path))
        if dry_run:
            output.write("".join(diffs))
        processed_paths.append(os.path.abspath(path))
    return processed_paths


def command_line(argv):
    """Instantiate an editor and process arguments.

    Optional argument:
      processed_paths: paths processed are appended to the list.
    """
    arguments = parse_command_line(argv)
    paths = edit_files(arguments.patterns,
                       expressions=arguments.expressions,
                       functions=arguments.functions,
                       executables=arguments.executables,
                       start_dir=arguments.start_dir,
                       max_depth=arguments.max_depth,
                       dry_run=arguments.dry_run,
                       output=arguments.output)
    # If the output is not sys.stdout, we need to close it because
    # argparse.FileType does not do it for us.
    if isinstance(arguments.output, io.IOBase):
        arguments.output.close()
    return paths


def main():
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    try:
        command_line(sys.argv)
    finally:
        logging.shutdown()


if __name__ == "__main__":
    sys.exit(main())
