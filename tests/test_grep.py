
import io
import unittest
from unittest.mock import patch, mock_open
from src.commands import GrepCommand
from src.parser import ParsedCommand


class TestGrepCommand(unittest.TestCase):
    def setUp(self):
        self.grep = GrepCommand()
        self.sample_text = """first line
second line
third line
fourth line
Fifth LINE
SIXTH line
seventh line
eighth line
special_chars: !@#$%^&*()
unicode: 你好 мир"""

    def test_grep_simple_pattern(self):
        cmd = ParsedCommand("grep", ["line"])
        exit_code, output = self.grep.execute(cmd, stdin=self.sample_text)
        self.assertEqual(exit_code, 0)
        self.assertIn("first line", output)
        self.assertIn("second line", output)
        self.assertNotIn("Fourth", output)

    def test_grep_word_flag(self):
        cmd = ParsedCommand("grep", ["-w", "line"])
        exit_code, output = self.grep.execute(cmd, stdin=self.sample_text)
        self.assertEqual(exit_code, 0)
        self.assertIn("first line", output)
        self.assertNotIn("Fifth LINE", output)

    def test_grep_case_insensitive(self):
        cmd = ParsedCommand("grep", ["-i", "fifth"])
        exit_code, output = self.grep.execute(cmd, stdin=self.sample_text)
        self.assertEqual(exit_code, 0)
        self.assertIn("Fifth LINE", output)

    def test_grep_after_context(self):
        cmd = ParsedCommand("grep", ["-A", "2", "third"])
        exit_code, output = self.grep.execute(cmd, stdin=self.sample_text)
        self.assertEqual(exit_code, 0)
        result_lines = output.split('\n')
        self.assertIn("third line", result_lines)
        self.assertIn("fourth line", result_lines)
        self.assertIn("Fifth LINE", result_lines)
        self.assertNotIn("second line", result_lines)

    def test_grep_combined_flags(self):
        cmd = ParsedCommand("grep", ["-i", "-w", "-A", "1", "sixth"])
        exit_code, output = self.grep.execute(cmd, stdin=self.sample_text)
        self.assertEqual(exit_code, 0)
        result_lines = output.split('\n')
        self.assertIn("SIXTH line", result_lines)
        self.assertIn("seventh line", result_lines)
        self.assertNotIn("eighth line", result_lines)

    def test_grep_special_chars(self):
        cmd = ParsedCommand("grep", ["!@"])
        exit_code, output = self.grep.execute(cmd, stdin=self.sample_text)
        self.assertEqual(exit_code, 0)
        self.assertIn("special_chars: !@#$%^&*()", output)

    def test_grep_unicode(self):
        cmd = ParsedCommand("grep", ["你好"])
        exit_code, output = self.grep.execute(cmd, stdin=self.sample_text)
        self.assertEqual(exit_code, 0)
        self.assertIn("unicode: 你好 мир", output)

    def test_grep_overlapping_context(self):
        cmd = ParsedCommand("grep", ["-A", "3", "line"])
        exit_code, output = self.grep.execute(cmd, stdin=self.sample_text)
        self.assertEqual(exit_code, 0)
        # Проверяем что строки не дублируются
        result_lines = output.split('\n')
        self.assertEqual(len(result_lines), len(set(result_lines)))

    def test_grep_file_input(self):
        test_content = self.sample_text
        with patch('builtins.open', mock_open(read_data=test_content)):
            cmd = ParsedCommand("grep", ["line", "test.txt"])
            exit_code, output = self.grep.execute(cmd)
            self.assertEqual(exit_code, 0)
            self.assertIn("first line", output)


class TestGrepIntegration(unittest.TestCase):
    def setUp(self):
        from src.executor import Executor
        from src.parser import Parser
        self.executor = Executor()
        self.parser = Parser()
        self.sample_text = """first match\nsecond line\nthird match\nfourth line"""

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_grep_in_pipeline(self, mock_stdout):
        from src.parser import Parser
        parser = Parser()

        input_str = "echo '{}' | grep match | wc".format(self.sample_text)
        parsed_input = parser.parse(input_str)

        exit_code = self.executor.execute(parsed_input)
        output = mock_stdout.getvalue().strip()

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "2 4 23")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_grep_with_flags_in_pipeline(self, mock_stdout):
        from src.parser import Parser
        parser = Parser()

        input_str = "echo '{}' | grep -i -A 1 MATCH".format(self.sample_text)
        parsed_input = parser.parse(input_str)

        exit_code = self.executor.execute(parsed_input)
        output_lines = mock_stdout.getvalue().strip().split('\n')

        self.assertEqual(exit_code, 0)
        self.assertIn("first match", output_lines)
        self.assertIn("second line", output_lines)
        self.assertIn("third match", output_lines)
        self.assertIn("fourth line", output_lines)
        self.assertEqual(len(output_lines), 4)


if __name__ == '__main__':
    unittest.main()
