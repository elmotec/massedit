#!/usr/bin/env python

"""Test module to test massedit."""

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

import os
import sys
import logging
import unittest
import mock

import massedit


def remove_module(module_name):
    """Removes the module from memory."""
    if module_name in sys.modules:
        del(sys.modules[module_name])


class TestEditor(unittest.TestCase):  # pylint: disable=R0904
    """Tests the massedit module."""

    def test_logger_error(self):
        """Tests logging from logger works at least for errors."""
        mock_handler = mock.Mock()
        mock_handler.level = logging.ERROR
        massedit.logger.addHandler(mock_handler)
        massedit.logger.error('test')
        self.assertTrue(mock_handler.handle.called)

    def test_no_change(self):
        """Tests the editor does nothing when not told to do anything."""
        editor = massedit.Editor()
        input_line = "some info"
        output_line = editor.edit_line(input_line)
        self.assertEqual(output_line, input_line)

    def test_simple_replace(self):
        """Simple replacement check."""
        editor = massedit.Editor()
        original_line = 'What a nice cat!'
        editor.append_code_expr("re.sub('cat','horse',line)")
        new_line = editor.edit_line(original_line)
        self.assertEqual(new_line, 'What a nice horse!')
        self.assertEqual(original_line, 'What a nice cat!')

    def test_syntax_error(self):
        """Checks we get a SyntaxError if the code is not valid."""
        editor = massedit.Editor()
        with self.assertRaises(SyntaxError):
            editor.append_code_expr("invalid expression")
            self.assertIsNone(editor.code_objs)

    def test_invalid_code_expr2(self):
        """Checks we get a SyntaxError if the code is missing an argument."""
        editor = massedit.Editor()
        editor.append_code_expr("re.sub('def test', 'def toast')")
        with self.assertRaises(massedit.EditorError):
            editor.edit_line('some line')

    @unittest.skip("FIXME. Will revisit this one.")
    def test_missing_module(self):
        """Checks that missing module generates an exception."""
        remove_module('random')
        self.assertNotIn('random', sys.modules)
        editor = massedit.Editor()
        #random.randint(0,10)  # Fails as it should.
        editor.append_code_expr('random.randint(0,10)')  # works ?!
        with self.assertRaises(NameError):
            editor.append_code_expr("random.randint(0,10)")  # Houston...

    def test_module_import(self):
        """Checks the module import functinality."""
        remove_module('random')
        editor = massedit.Editor()
        editor.import_module('random')
        editor.append_code_expr('random.randint(0,9)')
        random_number = editor.edit_line('to be replaced')
        self.assertIn(random_number, [str(x) for x in range(10)])


class TestEditorWithFile(unittest.TestCase):  # pylint: disable=R0904
    """Tests the command line interface of massedit.py."""
    def setUp(self):
        """Creates a temporary file to work with."""
        self.file = open("test_file.txt", "w")
        self.text = """The Zen of Python, by Tim Peters

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
        self.file.write(self.text)
        self.file.close()

    def tearDown(self):
        """Removes the temporary file."""
        os.unlink(self.file.name)

    def test_setup(self):
        """Checks that we have a temporary file to work with."""
        self.assertTrue(os.path.exists(self.file.name))

    def test_replace_in_file(self):
        """Checks editing of an entire file."""
        editor = massedit.Editor()
        editor.append_code_expr("re.sub('Dutch', 'Guido', line)")
        diffs = editor.edit_file(self.file.name)
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
        with mock.patch('sys.stdout') as mock_stdout:
            massedit.command_line(["massedit.py", "-w", "-e",
                "re.sub('Dutch', 'Guido', line)", self.file.name])
            new_lines = open(self.file.name, "r").readlines()
            original_lines = self.text.splitlines(True)
            self.assertEqual(len(new_lines), len(original_lines))
            n_lines = len(new_lines)
            for line in xrange(n_lines):
                if line != 16:
                    self.assertEqual(new_lines[line - 1],
                            original_lines[line - 1])
                else:
                    expected_line_16 = \
                        "Although that way may not be obvious " + \
                        "at first unless you're Guido.\n"
                    self.assertEqual(new_lines[line - 1], expected_line_16)
        self.assertFalse(mock_stdout.write.called)

    def test_command_line_check(self):
        """Checks simple replacement via command line."""
        with mock.patch('sys.stdout') as mock_stdout:
            massedit.command_line(["-e", "re.sub('Dutch', 'Guido', line)",
                self.file.name])
            new_lines = open(self.file.name, "r").readlines()
            original_lines = self.text.splitlines(True)
            self.assertEqual(original_lines, new_lines)
        self.assertTrue(mock_stdout.write.called)

if __name__ == "__main__":
    massedit.logger.removeHandler(massedit.logger.handlers[0])
    #massedit.logger.setLevel(logging.DEBUG)
    os_status = unittest.main(argv=sys.argv)
    sys.exit(os_status)
