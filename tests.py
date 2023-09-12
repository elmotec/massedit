#!/usr/bin/env python
# coding: utf-8

"""Test module to test massedit."""

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

import io
import logging
import os
import platform
import shutil
import sys
import tempfile
import textwrap
import unittest

import massedit

if sys.version_info < (3, 3):
    import mock  # pylint: disable=import-error

    builtins = "__builtin__"
else:
    from unittest import mock  # pylint: disable=import-error, no-name-in-module

    builtins = "builtins"


try:
    unicode
except NameError:
    unicode = str  # pylint: disable=invalid-name, redefined-builtin


zen = unicode(
    """The Zen of Python, by Tim Peters

Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
Now is better than never.
Although never is often better than *right* now.
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
"""
)


class Workspace:
    """Wraps creation of files/workspace.

    For some reason tempfile.mkdtemp() causes problems with Python 2.7:
      File "C:\\Python27\\lib\\random.py", line 113, in seed
        a = long(_hexlify(_urandom(2500)), 16)
    TypeError: 'NoneType' object is not callable

    """

    def __init__(self, parent_dir=None):
        """Initialize Temp class.

        Arguments:
          parent_dir (str): workspace where to create temporary files/dirs.

        If parent_dir is not given, uses tempfile pacakge to try to get a
        temporary directory. If that fails, use the current working directory.

        """

        if parent_dir is None:
            parent_dir = tempfile.tempdir
            if parent_dir is None:
                parent_dir = os.path.abspath(os.path.curdir)
        self.top_dir = self.get_directory(parent_dir=parent_dir)

    # Cannot use __del__ here because self.top_dir does not always exist
    # when _del__ is called: http://stackoverflow.com/questions/865115/
    def cleanup(self):
        """Delete temporary directories/files."""
        shutil.rmtree(self.top_dir)

    def get_base_name(self):
        """Create a base"""
        import binascii

        suffix = binascii.hexlify(os.urandom(4)).decode("ascii")
        return "massedit" + suffix

    def get_directory(self, parent_dir=None):
        """Create a temporary directory in parent_dir."""

        if parent_dir is None:
            parent_dir = self.top_dir
        dir_name = os.path.join(parent_dir, self.get_base_name())
        os.mkdir(dir_name)
        return dir_name

    def get_file(self, parent_dir=None, extension=None):
        """Get a new temporary file name."""

        if not parent_dir:
            parent_dir = self.top_dir
        file_name = os.path.join(parent_dir, self.get_base_name())
        if extension:
            file_name += extension
        return file_name


class LogInterceptor:  # pylint: disable=too-few-public-methods
    """Replaces all log handlers and redirect log to the stream."""

    def __init__(self, logger):
        """Sets up log handler for logger and remove all existing handlers.

        Arguments:
          logger (logging.Logger): logger to be modified.

        Sets up variables:
          self.__content (io.StringIO): stores the log.
          self.handler (logging.StreamHandler): handler for self.__content.
          self.logger (logging.Logger): the logger to intercept.

        """
        # Stores original values.
        self.__handlers = []
        self.__propagate = logger.propagate
        self.__content = io.StringIO()
        self.logger = logger
        self.logger.propagate = False
        self.handler = logging.StreamHandler(self.__content)
        for handler in logger.handlers:
            self.__handlers.append(handler)
            logger.removeHandler(handler)
        logger.addHandler(self.handler)

    @property
    def log(self):
        """Flush the handler and return the content of self.__content."""
        self.handler.flush()
        return self.__content.getvalue()

    def __del__(self):
        """Reset the handlers the way they were."""
        self.logger.removeHandler(self.handler)
        for hdlr in self.__handlers:
            self.logger.addHandler(hdlr)
        self.logger.propagate = self.__propagate


def dutch_is_guido(lines, _):
    """Helper function that substitute Dutch with Guido."""
    import re

    for line in lines:
        yield re.sub("Dutch", "Guido", line)


def remove_module(module_name):
    """Remove the module from memory."""
    if module_name in sys.modules:
        del sys.modules[module_name]


class TestGetFunction(unittest.TestCase):  # pylint: disable=R0904

    """Test the functon get_function."""

    def test_simple_retrieval(self):
        """test retrieval of function in argument string."""
        function = massedit.get_function("tests:dutch_is_guido")
        # Functions are not the same but the code is.
        self.assertEqual(dutch_is_guido.__code__, function.__code__)


class TestMassEdit(unittest.TestCase):  # pylint: disable=R0904

    """Test the massedit module."""

    def setUp(self):
        self.editor = massedit.MassEdit()

    def tearDown(self):
        del self.editor

    def test_no_change(self):
        """Test the editor does nothing when not told to do anything."""
        input_line = "some info"
        output_line = self.editor.edit_line(input_line)
        self.assertEqual(output_line, input_line)

    def test_simple_replace(self):
        """Simple replacement check."""
        original_line = "What a nice cat!"
        self.editor.append_code_expr("re.sub('cat','horse',line)")
        new_line = self.editor.edit_line(original_line)
        self.assertEqual(new_line, "What a nice horse!")
        self.assertEqual(original_line, "What a nice cat!")

    def test_replace_all(self):
        """Test replacement of an entire line."""
        original_line = "all of it"
        self.editor.append_code_expr("re.sub('all of it', '', line)")
        new_line = self.editor.edit_line(original_line)
        self.assertEqual(new_line, "")

    def test_syntax_error(self):
        """Check we get a SyntaxError if the code is not valid."""
        with mock.patch("massedit.log", autospec=True):
            with self.assertRaises(SyntaxError):
                self.editor.append_code_expr("invalid expression")
                self.assertIsNone(self.editor.code_objs)

    def test_invalid_code_expr2(self):
        """Check we get a SyntaxError if the code is missing an argument."""
        self.editor.append_code_expr("re.sub('def test', 'def toast')")
        massedit.log.disabled = True
        with self.assertRaises(TypeError):
            self.editor.edit_line("some line")
        massedit.log.disabled = False

    def test_missing_module(self):
        """Check that missing module generates an exception."""
        self.editor.append_code_expr("random.randint(0,10)")
        with self.assertRaises(NameError):
            self.editor.edit_line("need to edit a line to execute the code")

    def test_module_import(self):
        """Check the module import functinality."""
        remove_module("random")
        self.editor.import_module("random")
        self.editor.append_code_expr("random.randint(0,9)")
        random_number = self.editor.edit_line("to be replaced")
        self.assertIn(random_number, [str(x) for x in range(10)])

    def test_file_edit(self):
        """Simple replacement check."""
        original_file = zen.split("\n")
        self.editor.append_function(dutch_is_guido)
        actual_file = list(self.editor.edit_content(original_file, "filename"))
        expected_file = original_file
        expected_file[15] = (
            "Although that way may not be obvious " "at first unless you're Guido."
        )
        self.editor.max_diff = None
        self.assertEqual(actual_file, expected_file)


class TestMassEditWithFile(unittest.TestCase):

    """Test massedit with an actual file."""

    def setUp(self):
        self.editor = massedit.MassEdit()
        self.workspace = Workspace()
        self.file_name = os.path.join(self.workspace.top_dir, unicode("somefile.txt"))

    def tearDown(self):
        """Remove the temporary file."""
        self.workspace.cleanup()

    def write_input_file(self, text, encoding=None):
        """Write text in input file.

        :param encoding: defaults to utf-8

        """
        if not encoding:
            encoding = "utf-8"
        with io.open(self.file_name, "w+", encoding=encoding) as fh:
            fh.write(text)

    def test_non_utf8_with_utf8_setting(self):
        """Check files with non-utf8 characters are skipped with a warning."""
        log_sink = LogInterceptor(massedit.log)
        content = unicode("This is ok\nThis \u00F1ot")
        self.write_input_file(content, encoding="cp1252")

        def identity(lines, _):
            """Return the line itself."""
            for line in lines:
                yield line

        self.editor.append_function(identity)
        with self.assertRaises(UnicodeDecodeError):
            _ = self.editor.edit_file(self.file_name)
        self.assertIn("encoding error", log_sink.log)

    def test_handling_of_cp1252(self):
        """Check files with non-utf8 characters are skipped with a warning."""
        encoding = "cp1252"
        self.editor.encoding = encoding
        content = unicode("This is ok\nThis \u00F1ot")
        self.write_input_file(content, encoding=encoding)

        def identity(lines, _):
            """Return the line itself."""
            for line in lines:
                yield line

        self.editor.append_function(identity)
        diffs = self.editor.edit_file(self.file_name)
        self.assertEqual(diffs, [])

    def test_forcing_end_of_line_for_output_files(self):
        """Check files with CRLF are created with LF when using newline setting"""
        self.editor.newline = "\n"

        content = "This is a line finishing with CRLF\r\n"

        self.write_input_file(content)

        def identity(lines, _):
            """Return the line itself."""
            for line in lines:
                yield line

        self.editor.append_function(identity)
        diffs = self.editor.edit_file(self.file_name)

        self.assertEqual(diffs, [])

        with io.open(self.file_name) as f:
            f.readline()
            output_newline = f.newlines

        expected_eol = self.editor.newline
        if expected_eol is None:
            # If not specified use the string to terminate lines on the current platform
            expected_eol = os.linesep

        self.assertEqual(expected_eol, output_newline)


class TestMassEditWithZenFile(TestMassEditWithFile):  # pylint: disable=R0904

    """Test the command line interface of massedit.py with actual file."""

    def setUp(self):
        """Use zen of Python as content."""
        TestMassEditWithFile.setUp(self)
        self.write_input_file(zen)

    def test_setup(self):
        """Check that we have a temporary file to work with."""
        self.assertTrue(os.path.exists(self.file_name))

    def test_replace_in_file(self):
        """Check editing of an entire file."""
        self.editor.append_code_expr("re.sub('Dutch', 'Guido', line)")
        diffs = self.editor.edit_file(self.file_name)
        self.assertEqual(len(diffs), 11)
        expected_diffs = textwrap.dedent(
            """
         There should be one-- and preferably only one --obvious way to do it.
        -Although that way may not be obvious at first unless you're Dutch.
        +Although that way may not be obvious at first unless you're Guido.
         Now is better than never.\n"""
        )
        self.assertEqual("".join(diffs[5:9]), "".join(expected_diffs[1:]))

    def test_replace_cannot_backup(self):
        """Check replacement fails if backup fails."""
        self.editor.append_code_expr("re.sub('Dutch', 'Guido', line)")
        backup = self.file_name + ".bak"
        try:
            shutil.copy(self.file_name, backup)
            # FileExistsError in more recent version of Python.
            with self.assertRaises(OSError):
                self.editor.edit_file(self.file_name)
        finally:
            os.unlink(backup)

    def test_command_line_replace(self):
        """Check simple replacement via command line."""
        file_base_name = os.path.basename(self.file_name)
        massedit.command_line(
            [
                "massedit.py",
                "-w",
                "-e",
                "re.sub('Dutch', 'Guido', line)",
                "-w",
                "-s",
                self.workspace.top_dir,
                file_base_name,
            ]
        )
        with io.open(self.file_name, "r") as new_file:
            new_lines = new_file.readlines()
        original_lines = zen.splitlines(True)
        self.assertEqual(len(new_lines), len(original_lines))
        n_lines = len(new_lines)
        for line in range(n_lines):
            if line != 16:
                self.assertEqual(new_lines[line - 1], original_lines[line - 1])
            else:
                expected_line_16 = (
                    "Although that way may not be obvious "
                    + "at first unless you're Guido.\n"
                )
                self.assertEqual(new_lines[line - 1], expected_line_16)

    def test_command_line_check(self):
        """Check dry run via command line with start workspace option."""
        out_file_name = self.workspace.get_file()
        basename = os.path.basename(self.file_name)
        arguments = [
            "test",
            "-e",
            "re.sub('Dutch', 'Guido', line)",
            "-o",
            out_file_name,
            "-s",
            self.workspace.top_dir,
            basename,
        ]
        processed = massedit.command_line(arguments)
        self.assertEqual(processed, [os.path.abspath(self.file_name)])
        with io.open(self.file_name, "r") as updated_file:
            new_lines = updated_file.readlines()
        original_lines = zen.splitlines(True)
        self.assertEqual(original_lines, new_lines)
        self.assertTrue(os.path.exists(out_file_name))
        os.unlink(out_file_name)

    def test_absolute_path_arg(self):
        """Check dry run via command line with single file name argument."""
        out_file_name = self.workspace.get_file()
        arguments = [
            "massedit.py",
            "-e",
            "re.sub('Dutch', 'Guido', line)",
            "-o",
            out_file_name,
            self.file_name,
        ]
        processed = massedit.command_line(arguments)
        self.assertEqual(processed, [os.path.abspath(self.file_name)])
        with io.open(self.file_name, "r") as updated_file:
            new_lines = updated_file.readlines()
        original_lines = zen.splitlines(True)
        self.assertEqual(original_lines, new_lines)
        self.assertTrue(os.path.exists(out_file_name))
        os.unlink(out_file_name)

    def test_api(self):
        """Check simple replacement via api."""
        file_base_name = os.path.basename(self.file_name)
        processed = massedit.edit_files(
            [file_base_name],
            ["re.sub('Dutch', 'Guido', line)"],
            [],
            start_dirs=self.workspace.top_dir,
            dry_run=False,
        )
        self.assertEqual(processed, [self.file_name])
        with io.open(self.file_name, "r") as new_file:
            new_lines = new_file.readlines()
        original_lines = zen.splitlines(True)
        self.assertEqual(len(new_lines), len(original_lines))
        n_lines = len(new_lines)
        for line in range(n_lines):
            if line != 16:
                self.assertEqual(new_lines[line - 1], original_lines[line - 1])
            else:
                expected_line_16 = (
                    "Although that way may not be obvious "
                    + "at first unless you're Guido.\n"
                )
                self.assertEqual(new_lines[line - 1], expected_line_16)

    @unittest.skipIf(
        platform.system() == "Windows", "No exec bit for Python on windows"
    )
    def test_preserve_permissions(self):
        """Test that the exec bit is preserved when processing file."""
        import stat

        def is_executable(file_name):
            """Check if the file has the exec bit set."""
            return stat.S_IXUSR & os.stat(file_name)[stat.ST_MODE] > 0

        self.assertFalse(is_executable(self.file_name))
        mode = os.stat(self.file_name)[stat.ST_MODE] | stat.S_IEXEC
        # Windows supports READ and WRITE, but not EXEC bit.
        os.chmod(self.file_name, mode)
        self.assertTrue(is_executable(self.file_name))
        file_base_name = os.path.basename(self.file_name)
        massedit.command_line(
            [
                "massedit.py",
                "-w",
                "-e",
                "re.sub('Dutch', 'Guido', line)",
                "-w",
                "-s",
                self.workspace.top_dir,
                file_base_name,
            ]
        )
        statinfo = os.stat(self.file_name)
        self.assertEqual(statinfo.st_mode, mode)


class TestMassEditWalk(unittest.TestCase):  # pylint: disable=R0904

    """Test recursion when processing files."""

    def setUp(self):
        self.workspace = Workspace()
        self.subdirectory = self.workspace.get_directory()
        self.file_names = []
        for ii in range(3):
            file_name = self.workspace.get_file(
                parent_dir=self.subdirectory, extension=".txt"
            )
            with io.open(file_name, "w+") as fh:
                fh.write(unicode("some text ") + unicode(ii))
            self.file_names.append(file_name)

    def tearDown(self):
        self.workspace.cleanup()

    def test_feature(self):
        """Trivial test to make sure setUp and tearDown work."""
        pass

    def test_process_subdirectory_dry_run(self):
        """Check that ommiting -w option does not change the files."""
        output = io.StringIO()
        processed_files = massedit.edit_files(
            ["*.txt"],
            expressions=["re.sub('text', 'blah blah', line)"],
            start_dirs=self.workspace.top_dir,
            output=output,
        )
        self.assertEqual(sorted(processed_files), sorted(self.file_names))
        index = {}
        for ii, file_name in enumerate(self.file_names):
            with io.open(file_name) as fh:
                new_lines = fh.readlines()
            self.assertEqual(new_lines, ["some text " + unicode(ii)])
            index[file_name] = ii
        actual = output.getvalue()
        expected = "".join(
            [
                textwrap.dedent(
                    """\
                            --- {}
                            +++ <new>
                            @@ -1 +1 @@
                            -some text {}+some blah blah {}"""
                ).format(file_name, index[file_name], index[file_name])
                for file_name in processed_files
            ]
        )
        self.assertEqual(actual, expected)

    def test_process_subdirectory_dry_run_with_one_change(self):
        """Check that ommiting -w option does not change the files."""
        output = io.StringIO()
        processed_files = massedit.edit_files(
            ["*.txt"],
            expressions=["re.sub('text 1', 'blah blah 1', line)"],
            start_dirs=self.workspace.top_dir,
            output=output,
        )
        self.assertEqual(processed_files, self.file_names[1:2])
        index = {}
        for ii, file_name in enumerate(self.file_names):
            with io.open(file_name) as fh:
                new_lines = fh.readlines()
            self.assertEqual(new_lines, ["some text " + unicode(ii)])
            index[file_name] = ii
        actual = output.getvalue()
        expected = "".join(
            [
                textwrap.dedent(
                    """\
                            --- {}
                            +++ <new>
                            @@ -1 +1 @@
                            -some text {}+some blah blah {}"""
                ).format(file_name, index[file_name], index[file_name])
                for file_name in processed_files
            ]
        )
        self.assertEqual(actual, expected)

    def test_process_subdirectory(self):
        """Check that the editor works correctly in subdirectories."""
        arguments = [
            "-r",
            "-s",
            self.workspace.top_dir,
            "-w",
            "-e",
            "re.sub('text', 'blah blah', line)",
            "*.txt",
        ]
        processed_files = massedit.command_line(arguments)
        self.assertEqual(sorted(processed_files), sorted(self.file_names))
        for ii, file_name in enumerate(self.file_names):
            with io.open(file_name) as fh:
                new_lines = fh.readlines()
            self.assertEqual(new_lines, ["some blah blah " + unicode(ii)])

    def test_maxdepth_one(self):
        """Check that specifying -m 1 prevents modifiction to subdir."""
        arguments = [
            "-r",
            "-s",
            self.workspace.top_dir,
            "-w",
            "-e",
            "re.sub('text', 'blah blah', line)",
            "-m",
            "0",
            "*.txt",
        ]
        processed_files = massedit.command_line(arguments)
        self.assertEqual(processed_files, [])
        for ii, file_name in enumerate(self.file_names):
            with io.open(file_name) as fh:
                new_lines = fh.readlines()
            self.assertEqual(new_lines, ["some text " + unicode(ii)])


class TestIsList(unittest.TestCase):

    """Test the is_list function."""

    def test_single_element_list(self):
        """Base case."""
        self.assertTrue(massedit.is_list(["test"]))

    def test_empty_list(self):
        """Empty lists should work too."""
        self.assertTrue(massedit.is_list([]))

    def test_string_not_ok(self):
        """String should not be confused with lists"""
        self.assertFalse(massedit.is_list("test"))

    def test_unicode_string_not_ok(self):
        """String should not be confused with lists"""
        self.assertFalse(massedit.is_list(unicode("test")))


class TestCommandLine(unittest.TestCase):  # pylint: disable=R0904

    """Test handing of command line arguments."""

    def test_parse_expression(self):
        """Simple test to show expression is handled by parser."""
        expr_name = "re.subst('Dutch', 'Guido', line)"
        argv = ["massedit.py", "--expression", expr_name, "tests.py"]
        arguments = massedit.parse_command_line(argv)
        self.assertEqual(arguments.expressions, [expr_name])

    def test_parse_function(self):
        """Simple test to show function is handled by parser."""
        function_name = "tests:dutch_is_guido"
        argv = ["massedit.py", "--function", function_name, "tests.py"]
        arguments = massedit.parse_command_line(argv)
        self.assertEqual(arguments.functions, [function_name])

    def test_exception_on_bad_patterns(self):
        """Check edit_files raises an error string instead of a list."""
        with self.assertRaises(TypeError):
            massedit.edit_files("test", [], [])

    def test_file_option(self):
        """Test processing of a file."""

        def add_header(data, _):
            """Add header on top of the file."""
            yield "header on top\n"
            for line in data:
                yield line

        output = io.StringIO()
        massedit.edit_files(["tests.py"], [], [add_header], output=output)
        # third line shows the added header.
        actual = output.getvalue().split("\n")[3]
        expected = "+header on top"
        self.assertEqual(actual, expected)

    def test_bad_module(self):
        """Test error when a bad module is passed to the command."""
        log_sink = LogInterceptor(massedit.log)
        with self.assertRaises(ImportError):
            massedit.edit_files(["tests.py"], functions=["bong:modify"])
        expected = "failed to import bong\n"
        self.assertEqual(log_sink.log, expected)

    def test_empty_function(self):
        """Test empty argument."""
        log_sink = LogInterceptor(massedit.log)
        with self.assertRaises(AttributeError):
            massedit.edit_files(["tests.py"], functions=[":"])
        expected = (
            "':' is not a callable function: " + "'dict' object has no attribute ''\n"
        )
        self.assertEqual(log_sink.log, expected)

    def test_bad_function_name(self):
        """Check error when the function name is not valid."""
        log_sink = LogInterceptor(massedit.log)
        with self.assertRaises(AttributeError):
            massedit.edit_files(["tests.py"], functions=["massedit:bad_fun"])
        expected = "has no attribute 'bad_fun'\n"
        self.assertIn(expected, log_sink.log)

    def test_missing_function_name(self):
        """Check error when the function is empty but not the module."""
        log_sink = LogInterceptor(massedit.log)
        with self.assertRaises(AttributeError):
            massedit.edit_files(["tests.py"], functions=["massedit:"])
        expected = (
            "'massedit:' is not a callable function: "
            + "'dict' object has no attribute 'massedit'\n"
        )
        self.assertEqual(log_sink.log, expected)

    def test_wrong_number_of_argument(self):
        """Test passing function that has the wrong number of arguments."""
        log_sink = LogInterceptor(massedit.log)
        with self.assertRaises(ValueError):
            massedit.edit_files(["tests.py"], functions=["massedit:get_function"])
        expected = (
            "'massedit:get_function' is not a callable function: "
            + "function should take 2 arguments: lines, file_name\n"
        )
        self.assertEqual(log_sink.log, expected)

    def test_error_in_function(self):
        """Check error when the function triggers an exception."""

        def divide_by_zero(*_):
            """Simulates division by zero."""
            raise ZeroDivisionError()

        output = io.StringIO()
        massedit.log.disabled = True
        with self.assertRaises(ZeroDivisionError):
            massedit.edit_files(["tests.py"], [], [divide_by_zero], output=output)
        massedit.log.disabled = False

    def test_exec_option(self):
        """Check trivial call using executable."""
        output = io.StringIO()
        execname = "head -1"
        if platform.system() == "Windows":
            execname = "powershell -NoProfile -c gc -head 1"
        next(massedit.get_paths(["tests.py"]))
        massedit.edit_files(["tests.py"], executables=[execname], output=output)
        actual = output.getvalue().split("\n")
        self.assertEqual(actual[3], "-#!/usr/bin/env python")
        self.assertEqual(actual[-1], "+#!/usr/bin/env python+")

    def test_write_to_cp437_output(self):
        """Check writing to a cp437 output (e.g. Windows console)."""
        raw = io.BytesIO()
        output = io.TextIOWrapper(
            io.BufferedWriter(raw), encoding="cp437"
        )  # Windows console.
        massedit.edit_files(["tests.py"], expressions=["line[:10]"], output=output)
        actual = raw.getvalue()
        self.assertIsNotNone(actual)

    @mock.patch(builtins + ".open", new_callable=mock.mock_open)
    def test_generate_fixer(self, mock_open):
        """Generate a fixer template file with --generate option."""
        cmd = "massedit.py --generate fixer.py"
        massedit.command_line(cmd.split())
        mock_open.assert_called_with("fixer.py", "w+")
        mock_open().write.assert_called_with(massedit.fixer_template)

    @mock.patch("massedit.readlines", return_value=["some example text"])
    @mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_from_stdin(self, stdout_, _):
        """A simple dash reads input test from stdin."""
        # Note that double quotes will be interpreted by Python below.
        cmd = """massedit.py -e line.replace("text","test") -w -"""
        massedit.command_line(cmd.split())
        self.assertEqual("some example test", stdout_.getvalue())


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, level=logging.ERROR)
    try:
        unittest.main(argv=sys.argv)
    finally:
        logging.shutdown()
