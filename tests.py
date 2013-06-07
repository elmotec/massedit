#!/usr/bin/env python3
# vim: set encoding='utf-8'

"""Test module to test massedit."""

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

import os
import sys
import logging
import unittest
if sys.version_info < (3, 3):
    import mock
else:
    from unittest import mock
import tempfile
import io

import massedit


zen = """The Zen of Python, by Tim Peters

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


def dutch_is_guido(lines):
    """Helper function that substitute Dutch with Guido."""
    import re
    for line in lines:
        yield re.sub('Dutch', 'Guido', line)


def remove_module(module_name):
    """Removes the module from memory."""
    if module_name in sys.modules:
        del(sys.modules[module_name])


class TestGetFunction(unittest.TestCase):
    """Tests the functon get_function."""
    def test_simple_retrieval(self):
        function = massedit.get_function('tests:remove_module')
        # Functions are not the same but the code is.
        self.assertEqual(remove_module.__code__, function.__code__)


class TestEditor(unittest.TestCase):  # pylint: disable=R0904
    """Tests the massedit module."""

    def setUp(self):
        self.editor = massedit.Editor()

    def test_no_change(self):
        """Tests the editor does nothing when not told to do anything."""
        input_line = "some info"
        output_line = self.editor.edit_line(input_line)
        self.assertEqual(output_line, input_line)

    def test_simple_replace(self):
        """Simple replacement check."""
        original_line = 'What a nice cat!'
        self.editor.append_code_expr("re.sub('cat','horse',line)")
        new_line = self.editor.edit_line(original_line)
        self.assertEqual(new_line, 'What a nice horse!')
        self.assertEqual(original_line, 'What a nice cat!')

    def test_replace_all(self):
        """Tests replacement of an entire line."""
        original_line = 'all of it'
        self.editor.append_code_expr("re.sub('all of it', '', line)")
        new_line = self.editor.edit_line(original_line)
        self.assertEqual(new_line, '')

    def test_syntax_error(self):
        """Checks we get a SyntaxError if the code is not valid."""
        with mock.patch('massedit.log', auto_spec=True):
            with self.assertRaises(SyntaxError):
                self.editor.append_code_expr("invalid expression")
                self.assertIsNone(self.editor.code_objs)

    def test_invalid_code_expr2(self):
        """Checks we get a SyntaxError if the code is missing an argument."""
        self.editor.append_code_expr("re.sub('def test', 'def toast')")
        massedit.log.disabled = True
        with self.assertRaises(TypeError):
            self.editor.edit_line('some line')
        massedit.log.disabled = False

    @unittest.skip("FIXME. Will revisit this one.")
    def test_missing_module(self):
        """Checks that missing module generates an exception."""
        remove_module('random')
        self.assertNotIn('random', sys.modules)
        #random.randint(0,10)  # Fails as it should.
        self.editor.append_code_expr('random.randint(0,10)')  # works ?!
        with self.assertRaises(NameError):
            self.editor.append_code_expr("random.randint(0,10)")  # Houston...

    @unittest.skip("FIXME. remove_module causes problem with os.urandom.")
    def test_module_import(self):
        """Checks the module import functinality."""
        remove_module('random')
        self.editor.import_module('random')
        self.editor.append_code_expr('random.randint(0,9)')
        random_number = self.editor.edit_line('to be replaced')
        self.assertIn(random_number, [str(x) for x in range(10)])

    def test_file_edit(self):
        """Simple replacement check."""
        original_file = zen.split("\n")
        self.editor.append_function(dutch_is_guido)
        actual_file = list(self.editor.edit_content(original_file))
        expected_file = original_file
        expected_file[15] = "Although that way may not be obvious "\
                            "at first unless you're Guido."
        self.maxDiff = None
        self.assertEqual(actual_file, expected_file)


class TestEditorWithFile(unittest.TestCase):  # pylint: disable=R0904
    """Tests the command line interface of massedit.py."""
    def setUp(self):
        """Creates a temporary file to work with."""

        self.text = zen
        self.start_directory = tempfile.mkdtemp()
        self.file_name = os.path.join(self.start_directory, "somefile.txt")
        with open(self.file_name, "w+") as fh:
            fh.write(self.text)

    def tearDown(self):
        """Removes the temporary file."""
        os.unlink(self.file_name)
        os.rmdir(self.start_directory)

    def test_setup(self):
        """Checks that we have a temporary file to work with."""
        self.assertTrue(os.path.exists(self.file_name))

    def test_replace_in_file(self):
        """Checks editing of an entire file."""
        editor = massedit.Editor()
        editor.append_code_expr("re.sub('Dutch', 'Guido', line)")
        diffs = editor.edit_file(self.file_name)
        self.assertEqual(len(diffs), 11)
        expected_first_diff = """\
 There should be one-- and preferably only one --obvious way to do it.
-Although that way may not be obvious at first unless you're Dutch.
+Although that way may not be obvious at first unless you're Guido.
 Now is better than never.
"""
        self.assertEqual("".join(diffs[5:9]), expected_first_diff)

    def test_command_line_replace(self):
        """Checks simple replacement via command line."""
        file_base_name = os.path.basename(self.file_name)
        massedit.command_line(["massedit.py", "-w", "-e",
                               "re.sub('Dutch', 'Guido', line)",
                               "-w", "-s", self.start_directory,
                               file_base_name])
        with open(self.file_name, "r") as new_file:
            new_lines = new_file.readlines()
        original_lines = self.text.splitlines(True)
        self.assertEqual(len(new_lines), len(original_lines))
        n_lines = len(new_lines)
        for line in range(n_lines):
            if line != 16:
                self.assertEqual(new_lines[line - 1],
                                 original_lines[line - 1])
            else:
                expected_line_16 = \
                    "Although that way may not be obvious " + \
                    "at first unless you're Guido.\n"
                self.assertEqual(new_lines[line - 1], expected_line_16)

    def test_command_line_check(self):
        """Checks dry run via command line with start directory option."""
        out_file_name = tempfile.mktemp()
        basename = os.path.basename(self.file_name)
        arguments = ["test", "-e", "re.sub('Dutch', 'Guido', line)",
                     "-o", out_file_name, "-s", self.start_directory,
                     basename]
        processed = massedit.command_line(arguments)
        self.assertEqual(processed,
                         [os.path.abspath(self.file_name)])
        with open(self.file_name, "r") as updated_file:
            new_lines = updated_file.readlines()
        original_lines = self.text.splitlines(True)
        self.assertEqual(original_lines, new_lines)
        self.assertTrue(os.path.exists(out_file_name))
        os.unlink(out_file_name)

    def test_absolute_path_arg(self):
        """Checks dry run via command line with single file name argument."""
        out_file_name = tempfile.mktemp()
        arguments = ["massedit.py", "-e", "re.sub('Dutch', 'Guido', line)",
                     "-o", out_file_name, self.file_name]
        processed = massedit.command_line(arguments)
        self.assertEqual(processed,
                         [os.path.abspath(self.file_name)])
        with open(self.file_name, "r") as updated_file:
            new_lines = updated_file.readlines()
        original_lines = self.text.splitlines(True)
        self.assertEqual(original_lines, new_lines)
        self.assertTrue(os.path.exists(out_file_name))
        os.unlink(out_file_name)

    def test_api(self):
        """Checks simple replacement via api."""
        file_base_name = os.path.basename(self.file_name)
        processed = massedit.edit_files([file_base_name],
                                        ["re.sub('Dutch', 'Guido', line)"],
                                        [], start_dir=self.start_directory,
                                        dry_run=False)
        self.assertEqual(processed, [self.file_name])
        with open(self.file_name, "r") as new_file:
            new_lines = new_file.readlines()
        original_lines = self.text.splitlines(True)
        self.assertEqual(len(new_lines), len(original_lines))
        n_lines = len(new_lines)
        for line in range(n_lines):
            if line != 16:
                self.assertEqual(new_lines[line - 1],
                                 original_lines[line - 1])
            else:
                expected_line_16 = \
                    "Although that way may not be obvious " + \
                    "at first unless you're Guido.\n"
                self.assertEqual(new_lines[line - 1], expected_line_16)


class TestEditorWalk(unittest.TestCase):  # pylint: disable=R0904
    """Tests recursion when processing files."""

    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.subdirectory = os.path.join(self.directory, "subdir")
        os.mkdir(self.subdirectory)
        self.file_name = os.path.join(self.subdirectory, "somefile.txt")
        with open(self.file_name, "w+") as fh:
            fh.write("some text")

    def tearDown(self):
        os.unlink(self.file_name)
        os.rmdir(self.subdirectory)
        os.rmdir(self.directory)

    def test_feature(self):
        """Trivial test to make sure setUp and tearDown work."""
        pass

    def test_process_subdirectory(self):
        """Checks that the editor works correctly in subdirectories."""
        arguments = ["-r", "-s", self.directory, "-w",
                     "-e",  "re.sub('text', 'blah blah', line)",
                     "*.txt"]
        processed_files = massedit.command_line(arguments)
        self.assertEqual(processed_files, [self.file_name])
        with open(self.file_name) as fh:
            new_lines = fh.readlines()
        self.assertEqual(new_lines, ["some blah blah"])

    def test_maxdepth_one(self):
        """Checks that specifying -m 1 prevents modifiction to subdir."""
        arguments = ["-r", "-s", self.directory, "-w",
                     "-e",  "re.sub('text', 'blah blah', line)",
                     "-m", "0", "*.txt"]
        processed_files = massedit.command_line(arguments)
        self.assertEqual(processed_files, [])
        with open(self.file_name) as fh:
            new_lines = fh.readlines()
        self.assertEqual(new_lines, ["some text"])


class TestCommandLine(unittest.TestCase):
    def test_parse_expression(self):
        expr_name = "re.subst('Dutch', 'Guido', line)"
        argv = ["massedit.py", "--expression", expr_name, "tests.py"]
        arguments = massedit.parse_command_line(argv)
        self.assertEqual(arguments.expressions, [expr_name])

    def test_parse_function(self):
        function_name = "tests:dutch_is_guido"
        argv = ["massedit.py", "--function", function_name, "tests.py"]
        arguments = massedit.parse_command_line(argv)
        self.assertEqual(arguments.functions, [function_name])

    def test_exception_on_bad_patterns(self):
        """edit_files raises an error if we pass a string instead of a list."""
        with self.assertRaises(TypeError):
            massedit.edit_files('test', [], [])

    def test_file_option(self):
        def add_header(data):
            import re
            yield "header on top\n"
            for line in data:
                yield line
        output = io.StringIO()
        massedit.edit_files(['tests.py'], [], [add_header], output=output)
        # third line shows the added header.
        actual = output.getvalue().split("\n")[3]
        expected = "+header on top"
        self.assertEqual(actual, expected)

    def test_bad_function(self):
        def divide_by_zero(data):
            1 / 0
        output = io.StringIO()
        massedit.log.disabled = True
        with self.assertRaises(ZeroDivisionError):
            massedit.edit_files(['tests.py'], [], [divide_by_zero],
                                output=output)
        massedit.log.disabled = False


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, level=logging.ERROR)
    try:
        unittest.main(argv=sys.argv)
    finally:
        logging.shutdown()
