#!/usr/bin/env python

"""Test module to test massedit."""

import os
import sys
import unittest
import logging.config

import massedit

def configure_logging():
    """Configures logging."""
    logging_settings = {
    'version': 1,
    __name__: {
        'handlers': ['file', 'console'],
        'level': 'INFO',
        'propagate': 1,
        },
    'handlers': {
        'file': {
        'class': 'logging.FileHandler',
        'formatter': 'default',
        'filename': 'estimate.log',
        'level': 'INFO',
        },
        'console': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stderr',
        'formatter': 'default',
        'level': 'WARNING',
        },
        },
    'formatters': {
        'default': {
        'format': 'File "%(pathname)s", line %(lineno)d, '
                '%(name)s:%(levelname)s %(message)s',
        }
        }
    }
    logging.config.dictConfig(logging_settings)


def get_logger():
    configure_logging()
    logger = logging.getLogger(__name__)
    return logger


logger = get_logger()


class TestEditor(unittest.TestCase):  # pylint: disable=R0904
    """Tests the massedit module."""
    def test_no_change(self):
        """Tests the editor does nothing when not told to do anything."""
        editor = massedit.Editor()
        input_line = "some info"
        output_line = editor.edit_line(input_line)
        self.assertEquals(output_line, input_line)

    def test_simple_replace(self):
        """Simple replacement check."""
        editor = massedit.Editor()
        original_line = 'What a nice cat!'
        editor.set_code_expr("re.sub('cat','horse',line)")
        new_line = editor.edit_line(original_line)
        self.assertEquals(new_line, 'What a nice horse!')
        self.assertEquals(original_line, 'What a nice cat!')

    def test_syntax_error(self):
        """Checks we get a SyntaxError if the code is not valid."""
        editor = massedit.Editor()
        with self.assertRaises(SyntaxError):
            editor.set_code_expr("invalid expression")
            self.assertIsNone(self.code_obj)

    def test_invalid_code_expr2(self):
        """Checks we get a SyntaxError if the code is not valid."""
        editor = massedit.Editor()
        editor.set_code_expr("re.sub('def test', 'def toast')")
        with self.assertRaises(massedit.EditorError):
            editor.edit_line('some line')

    def remove_module(self, module_name):
        """Removes the module from memory."""
        if module_name in sys.modules:
            del(sys.modules[module_name])

    @unittest.skip("FIXME. Will revisit this one.")
    def test_missing_module(self):
        """Checks that missing module generates an exception."""
        self.remove_module('random')
        self.assertNotIn('random', sys.modules)
        editor = massedit.Editor()
        #random.randint(0,10)  # Fails as it should.
        editor.set_code_expr('random.randint(0,10)')  # This seems to work ?!
        with self.assertRaises(NameError):
            editor.set_code_expr("random.randint(0,10)")  # Houston...

    def test_module_import(self):
        """Checks the module import functinality."""
        self.remove_module('random')
        editor = massedit.Editor()
        editor.set_module('random')
        editor.set_code_expr('random.randint(0,9)')
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
        editor.set_code_expr("re.sub('Dutch', 'Guido', line)")
        diffs = editor.edit_file(self.file.name)
        self.assertEquals(len(diffs), 11)
        expected_first_diff = """\
 There should be one-- and preferably only one --obvious way to do it.
-Although that way may not be obvious at first unless you're Dutch.
+Although that way may not be obvious at first unless you're Guido.
 Now is better than never.
"""
        self.assertEquals("".join(diffs[5:9]), expected_first_diff)

    def test_command_line_replace(self):
        """Checks simple replacement via command line."""
        massedit.command_line(["-e","re.sub('Dutch', 'Guido', line)",
            self.file.name])
        new_lines = open(self.file.name, "r").readlines()
        original_lines = self.text.splitlines(True)
        length = max(len(new_lines), len(original_lines))
        for index in xrange(length):
            line = index + 1
            if line != 16:
                self.assertEquals(new_lines[index], original_lines[index])
            else:
                expected_line_16 = "Although that way may not be obvious " + \
                        "at first unless you're Guido.\n"
                self.assertEquals(new_lines[index], expected_line_16)

    def test_command_line_check(self):
        """Checks simple replacement via command line."""
        massedit.command_line(["-e","re.sub('Dutch', 'Guido', line)",
            self.file.name, "--check"])
        new_lines = open(self.file.name, "r").readlines()
        original_lines = self.text.splitlines(True)
        self.assertEquals(original_lines, new_lines)


if __name__ == "__main__":
    os_status = unittest.main(argv=sys.argv)
    sys.exit(os_status)
