#!/usr/bin/env python
# encoding: utf-8

"""A python bulk editor class to apply the same code to many files."""

# Copyright (c) 2012-17 Jérôme Lecomte
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


import os
import shutil
import sys
import logging
import argparse
import difflib
import re  # For convenience, pylint: disable=W0611
import fnmatch
import io
import subprocess
import textwrap


__version__ = '0.68.4'  # UPDATE setup.py when changing version.
__author__ = 'Jérôme Lecomte'
__license__ = 'MIT'


log = logging.getLogger(__name__)


try:
    unicode
except NameError:
    unicode = str  # pylint: disable=invalid-name, redefined-builtin


def is_list(arg):
    """Factor determination if arg is a list.

    Small utility for a better diagnostic because str/unicode are also
    iterable.

    """
    return iter(arg) and not isinstance(arg, unicode)


def get_function(fn_name):
    """Retrieve the function defined by the function_name.

    Arguments:
      fn_name: specification of the type module:function_name.

    """
    module_name, callable_name = fn_name.split(':')
    current = globals()
    if not callable_name:
        callable_name = module_name
    else:
        import importlib
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            log.error("failed to import %s", module_name)
            raise
        current = module
    for level in callable_name.split('.'):
        current = getattr(current, level)
    code = current.__code__
    if code.co_argcount != 2:
        raise ValueError('function should take 2 arguments: lines, file_name')
    return current


class MassEdit(object):

    """Mass edit lines of files."""

    def __init__(self, **kwds):
        """Initialize MassEdit object.

        Args:
          - code (byte code object): code to execute on input file.
          - function (str or callable): function to call on input file.
          - module (str): module name where to find the function.
          - executable (str): executable file name to execute on input file.
          - dry_run (bool): skip actual modification of input file if True.

        """
        self.code_objs = dict()
        self._codes = []
        self._functions = []
        self._executables = []
        self.dry_run = None
        self.encoding = 'utf-8'
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
        if 'encoding' in kwds:
            self.encoding = kwds['encoding']

    @staticmethod
    def import_module(module):  # pylint: disable=R0201
        """Import module that are needed for the code expr to compile.

        Argument:
          module (str or list): module(s) to import.

        """
        if isinstance(module, list):
            all_modules = module
        else:
            all_modules = [module]
        for mod in all_modules:
            globals()[mod] = __import__(mod.strip())

    @staticmethod
    def __edit_line(line, code, code_obj):  # pylint: disable=R0201
        """Edit a line with one code object built in the ctor."""
        try:
            # pylint: disable=eval-used
            result = eval(code_obj, globals(), locals())
        except TypeError as ex:
            log.error("failed to execute %s: %s", code, ex)
            raise
        if result is None:
            log.error("cannot process line '%s' with %s", line, code)
            raise RuntimeError('failed to process line')
        elif isinstance(result, list) or isinstance(result, tuple):
            line = unicode(' '.join([unicode(res_element)
                                     for res_element in result]))
        else:
            line = unicode(result)
        return line

    def edit_line(self, line):
        """Edit a single line using the code expression."""
        for code, code_obj in self.code_objs.items():
            line = self.__edit_line(line, code, code_obj)
        return line

    def edit_content(self, original_lines, file_name):
        """Processes a file contents.

        First processes the contents line by line applying the registered
        expressions, then process the resulting contents using the
        registered functions.

        Arguments:
          original_lines (list of str): file content.
          file_name (str): name of the file.

        """
        lines = [self.edit_line(line) for line in original_lines]
        for function in self._functions:
            try:
                lines = list(function(lines, file_name))
            except UnicodeDecodeError as err:
                log.error('failed to process %s: %s', file_name, err)
                return lines
            except Exception as err:
                log.error("failed to process %s with code %s: %s",
                          file_name, function, err)
                raise  # Let the exception be handled at a higher level.
        return lines

    def edit_file(self, file_name):
        """Edit file in place, returns a list of modifications (unified diff).

        Arguments:
          file_name (str, unicode): The name of the file.

        """
        with io.open(file_name, "r", encoding=self.encoding) as from_file:
            try:
                from_lines = from_file.readlines()
            except UnicodeDecodeError as err:
                log.error("encoding error (see --encoding): %s", err)
                raise

        if self._executables:
            nb_execs = len(self._executables)
            if nb_execs > 1:
                log.warn("found %d executables. Will use first one", nb_execs)
            exec_list = self._executables[0].split()
            exec_list.append(file_name)
            try:
                log.info("running %s...", " ".join(exec_list))
                output = subprocess.check_output(exec_list,
                                                 universal_newlines=True)
            except Exception as err:
                log.error("failed to execute %s: %s", " ".join(exec_list), err)
                raise  # Let the exception be handled at a higher level.
            to_lines = output.split(unicode("\n"))
        else:
            to_lines = from_lines

        # unified_diff wants structure of known length. Convert to a list.
        to_lines = list(self.edit_content(to_lines, file_name))
        diffs = difflib.unified_diff(from_lines, to_lines,
                                     fromfile=file_name, tofile='<new>')
        if not self.dry_run:
            bak_file_name = file_name + ".bak"
            if os.path.exists(bak_file_name):
                msg = "{} already exists".format(bak_file_name)
                if sys.version_info < (3, 3):
                    raise OSError(msg)
                else:
                    # noinspection PyCompatibility
                    # pylint: disable=undefined-variable
                    raise FileExistsError(msg)
            try:
                os.rename(file_name, bak_file_name)
                with io.open(file_name, 'w', encoding=self.encoding) as new:
                    new.writelines(to_lines)
                # Keeps mode of original file.
                shutil.copymode(bak_file_name, file_name)
            except Exception as err:
                log.error("failed to write output to %s: %s", file_name, err)
                # Try to recover...
                try:
                    os.rename(bak_file_name, file_name)
                except OSError as err:
                    log.error("failed to restore %s from %s: %s",
                              file_name, bak_file_name, err)
                raise
            try:
                os.unlink(bak_file_name)
            except OSError as err:
                log.warning("failed to remove backup %s: %s",
                            bak_file_name, err)
        return list(diffs)

    def append_code_expr(self, code):
        """Compile argument and adds it to the list of code objects."""
        # expects a string.
        if isinstance(code, str) and not isinstance(code, unicode):
            code = unicode(code)
        if not isinstance(code, unicode):
            raise TypeError("string expected")
        log.debug("compiling code %s...", code)
        try:
            code_obj = compile(code, '<string>', 'eval')
            self.code_objs[code] = code_obj
        except SyntaxError as syntax_err:
            log.error("cannot compile %s: %s", code, syntax_err)
            raise
        log.debug("compiled code %s", code)

    def append_function(self, function):
        """Append the function to the list of functions to be called.

        If the function is already a callable, use it. If it's a type str
        try to interpret it as [module]:?<callable>, load the module
        if there is one and retrieve the callable.

        Argument:
          function (str or callable): function to call on input.

        """
        if not hasattr(function, '__call__'):
            function = get_function(function)
            if not hasattr(function, '__call__'):
                raise ValueError("function is expected to be callable")
        self._functions.append(function)
        log.debug("registered %s", function.__name__)

    def append_executable(self, executable):
        """Append san executable os command to the list to be called.

        Argument:
          executable (str): os callable executable.

        """
        if isinstance(executable, str) and not isinstance(executable, unicode):
            executable = unicode(executable)
        if not isinstance(executable, unicode):
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
        """Check functions passed as argument and set them to be used."""
        for func in functions:
            try:
                self.append_function(func)
            except (ValueError, AttributeError) as ex:
                log.error("'%s' is not a callable function: %s", func, ex)
                raise

    def set_executables(self, executables):
        """Check and set the executables to be used."""
        for exc in executables:
            self.append_executable(exc)


def parse_command_line(argv):
    """Parse command line argument. See -h option.

    Arguments:
      argv: arguments on the command line must include caller file name.

    """
    import textwrap

    example = textwrap.dedent("""
    Examples:
    # Simple string substitution (-e). Will show a diff. No changes applied.
    {0} -e "re.sub('failIf', 'assertFalse', line)" *.py

    # File level modifications (-f). Overwrites the files in place (-w).
    {0} -w -f fixer:fixit *.py

    # Will change all test*.py in subdirectories of tests.
    {0} -e "re.sub('failIf', 'assertFalse', line)" -s tests test*.py
    """).format(os.path.basename(argv[0]))
    formatter_class = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description="Python mass editor",
                                     epilog=example,
                                     formatter_class=formatter_class)
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s {}".format(__version__))
    parser.add_argument("-w", "--write", dest="dry_run",
                        action="store_false", default=True,
                        help="modify target file(s) in place. "
                        "Shows diff otherwise.")
    parser.add_argument("-v", "--verbose", dest="verbose_count",
                        action="count", default=0,
                        help="increases log verbosity (can be specified "
                        "multiple times)")
    parser.add_argument("-e", "--expression", dest="expressions", nargs=1,
                        help="Python expressions applied to target files. "
                        "Use the line variable to reference the current line.")
    parser.add_argument("-f", "--function", dest="functions", nargs=1,
                        help="Python function to apply to target file. "
                        "Takes file content as input and yield lines. "
                        "Specify function as [module]:?<function name>.")
    parser.add_argument("-x", "--executable", dest="executables", nargs=1,
                        help="Python executable to apply to target file.")
    parser.add_argument("-s", "--start", dest="start_dirs",
                        help="Directory(ies) from which to look for targets.")
    parser.add_argument("-m", "--max-depth-level", type=int, dest="max_depth",
                        help="Maximum depth when walking subdirectories.")
    parser.add_argument("-o", "--output", metavar="FILE",
                        type=argparse.FileType("w"), default=sys.stdout,
                        help="redirect output to a file")
    parser.add_argument("-g", "--generate", metavar="FILE", type=str,
                        help="generate input file suitable for -f option")
    parser.add_argument("--encoding", dest="encoding",
                        help="Encoding of input and output files")
    parser.add_argument("patterns", metavar="pattern",
                        nargs="*",  # argparse.REMAINDER,
                        help="shell-like file name patterns to process.")
    arguments = parser.parse_args(argv[1:])

    if not (arguments.expressions or
            arguments.functions or
            arguments.generate or
            arguments.executables):
        parser.error(
            '--expression, --function, --generate or --executable missing')

    # Sets log level to WARN going more verbose for each new -V.
    log.setLevel(max(3 - arguments.verbose_count, 0) * 10)
    return arguments


def get_paths(patterns, start_dirs=None, max_depth=1):
    """Retrieve files that match any of the patterns."""
    # Shortcut: if there is only one pattern, make sure we process just that.
    if len(patterns) == 1 and not start_dirs:
        pattern = patterns[0]
        directory = os.path.dirname(pattern)
        if directory:
            patterns = [os.path.basename(pattern)]
            start_dirs = directory
            max_depth = 1

    if not start_dirs or start_dirs == '.':
        start_dirs = os.getcwd()
    for start_dir in start_dirs.split(','):
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


fixer_template = """\
#!/usr/bin/env python

def fixit(lines, file_name):
    '''Edit files passed to massedit

    :param list(str) lines: list of lines contained in the input file
    :param str file_name: name of the file the lines were read from

    :return: modified lines
    :rtype: list(str)

    Please modify the logic below (it does not change anything right now)
    and apply your logic to the in your directory like this:

    massedit -f <file name>:fixit files_to_modify\*

    See massedit -h for help and other options.

    '''
    changed_lines = []
    for lineno, line in enumerate(lines):
        changed_lines.append(line)
    return changed_lines


"""

def generate_fixer_file(output):
    """Generate a template fixer file to be used with --function option."""
    with open(output, "w+") as fh:
        fh.write(fixer_template)
    return


# pylint: disable=too-many-arguments, too-many-locals
def edit_files(patterns, expressions=None,
               functions=None, executables=None,
               start_dirs=None, max_depth=1, dry_run=True,
               output=sys.stdout, encoding=None):
    """Process patterns with MassEdit.

    Arguments:
      patterns: file pattern to identify the files to be processed.
      expressions: single python expression to be applied line by line.
      functions: functions to process files contents.
      executables: os executables to execute on the argument files.

    Keyword arguments:
      max_depth: maximum recursion level when looking for file matches.
      start_dirs: workspace(ies) where to start the file search.
      dry_run: only display differences if True. Save modified file otherwise.
      output: handle where the output should be redirected.

    Return:
      list of files processed.

    """
    if not is_list(patterns):
        raise TypeError("patterns should be a list")
    if expressions and not is_list(expressions):
        raise TypeError("expressions should be a list of exec expressions")
    if functions and not is_list(functions):
        raise TypeError("functions should be a list of functions")
    if executables and not is_list(executables):
        raise TypeError("executables should be a list of program names")

    editor = MassEdit(dry_run=dry_run, encoding=encoding)
    if expressions:
        editor.set_code_exprs(expressions)
    if functions:
        editor.set_functions(functions)
    if executables:
        editor.set_executables(executables)

    processed_paths = []
    for path in get_paths(patterns, start_dirs=start_dirs,
                          max_depth=max_depth):
        try:
            diffs = list(editor.edit_file(path))
            if dry_run:
                # At this point, encoding is the input encoding.
                diff = "".join(diffs)
                if not diff:
                    continue
                # The encoding of the target output may not match the input
                # encoding. If it's defined, we round trip the diff text
                # to bytes and back to silence any conversion errors.
                encoding = output.encoding
                if encoding:
                    bytes_diff = diff.encode(encoding=encoding, errors='ignore')
                    diff = bytes_diff.decode(encoding=output.encoding)
                output.write(diff)
        except UnicodeDecodeError as err:
            log.error("failed to process %s: %s", path, err)
            continue
        processed_paths.append(os.path.abspath(path))
    return processed_paths


def command_line(argv):
    """Instantiate an editor and process arguments.

    Optional argument:
      - processed_paths: paths processed are appended to the list.

    """
    arguments = parse_command_line(argv)
    if arguments.generate:
        generate_fixer_file(arguments.generate)
    paths = edit_files(arguments.patterns,
                       expressions=arguments.expressions,
                       functions=arguments.functions,
                       executables=arguments.executables,
                       start_dirs=arguments.start_dirs,
                       max_depth=arguments.max_depth,
                       dry_run=arguments.dry_run,
                       output=arguments.output,
                       encoding=arguments.encoding)
    # If the output is not sys.stdout, we need to close it because
    # argparse.FileType does not do it for us.
    is_sys = arguments.output in [sys.stdout, sys.stderr]
    if not is_sys and isinstance(arguments.output, io.IOBase):
        arguments.output.close()
    return paths


def main():
    """Main function."""
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    try:
        command_line(sys.argv)
    finally:
        logging.shutdown()


if __name__ == "__main__":
    sys.exit(main())
