#!/usr/bin/env python

"""Test module to test massedit."""

import unittest
import massedit


def get_current_file_name():
    import inspect
    current_path = inspect.getfile(inspect.currentframe()) 
    return current_path

class TestSed(unittest.TestCase):  # pylint: disable=R0904
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

    def test_invalid_code_expr2(self):
        """Checks we get a SyntaxError if the code is not valid."""
        editor = massedit.Editor()
        editor.set_code_expr("re.sub('def test', 'def toast')")
        with self.assertRaises(massedit.EditorError):
            new_line = editor.edit_line('some line')

    def remove_module(self, module_name):
        """Removes the module from memory."""
        import sys
        if module_name in sys.modules:
            del(sys.modules[module_name])

    @unittest.skip("FIXME. Will revisit this one.")
    def test_missing_module(self):
        """Checks that missing module generates an exception."""
        import sys
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
        self.assertIn(random_number, [ str(x) for x in range(10) ])

    def test_replace_in_file(self):
        """Checks editing of an entire file."""
        current_file_name = get_current_file_name()
        # This should get replaced when we self-process (1)
        editor = massedit.Editor()
        # This should get replaced when we self-process (2)
        editor.set_code_expr(
                "re.sub('self-process', 'process ourselves', line)") #  (3)
        diffs = editor.edit_file(
                current_file_name, dry_run=True)
        self.assertEquals(len(diffs), 24)
        expected_first_diff = """\
         current_file_name = get_current_file_name()
-        # This should get replaced when we self-process (1)
+        # This should get replaced when we process ourselves (1)
         editor = massedit.Editor()
"""
        self.assertEquals("".join(diffs[5:9]),expected_first_diff)


if __name__ == "__main__":
    import sys
    os_status = unittest.main(argv=sys.argv)
    sys.exit(os_status)
