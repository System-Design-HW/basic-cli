import unittest
import os
import tempfile
import io
from unittest.mock import patch
from src.parser import ParseError, Parser, ParsedInput, ParsedCommand
from src.executor import Executor


class TestParser(unittest.TestCase):
    def setUp(self):
        os.environ['TEST_VAR'] = 'test_value'

    def tearDown(self):
        del os.environ['TEST_VAR']

    def test_parse_simple_command(self):
        parser = Parser()
        result = parser.parse("echo hello world")
        self.assertEqual(len(result.commands), 1)
        self.assertEqual(result.commands[0].command_name, "echo")
        self.assertEqual(result.commands[0].args, ["hello", "world"])

    def test_parse_pipe_commands(self):
        parser = Parser()
        result = parser.parse("echo hello | wc")
        self.assertEqual(len(result.commands), 2)
        self.assertEqual(result.commands[0].command_name, "echo")
        self.assertEqual(result.commands[0].args, ["hello"])
        self.assertEqual(result.commands[1].command_name, "wc")
        self.assertEqual(result.commands[1].args, [])

    def test_parse_multiple_pipes(self):
        parser = Parser()
        result = parser.parse("echo hello | cat | wc")
        self.assertEqual(len(result.commands), 3)
        self.assertEqual(result.commands[0].command_name, "echo")
        self.assertEqual(result.commands[1].command_name, "cat")
        self.assertEqual(result.commands[2].command_name, "wc")

    def test_parse_variable_substitution(self):
        parser = Parser()
        result = parser.parse("echo $TEST_VAR")
        self.assertEqual(result.commands[0].args, ["test_value"])

    def test_parse_braced_variable_substitution(self):
        parser = Parser()
        result = parser.parse("echo ${TEST_VAR}")
        self.assertEqual(result.commands[0].args, ["test_value"])

    def test_parse_quoted_variables(self):
        parser = Parser()
        result = parser.parse('echo "$TEST_VAR"')
        self.assertEqual(result.commands[0].args, ["test_value"])

    def test_parse_empty_input(self):
        parser = Parser()
        with self.assertRaises(ParseError):
            parser.parse("")

    def test_parse_quoted_arguments(self):
        parser = Parser()
        result = parser.parse("echo 'hello world'")
        self.assertEqual(result.commands[0].args, ["hello world"])

    def test_parse_double_quoted_arguments(self):
        parser = Parser()
        result = parser.parse('echo "hello world"')
        self.assertEqual(result.commands[0].args, ["hello world"])


class TestExecutor(unittest.TestCase):
    def setUp(self):
        self.executor = Executor()
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.write(b"line1\nline2\nline3")
        self.temp_file.close()

    def tearDown(self):
        os.unlink(self.temp_file.name)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_execute_single_command(self, mock_stdout):
        commands = ParsedInput(commands=[
            ParsedCommand("echo", ["test"])
        ])
        exit_code = self.executor.execute(commands)
        self.assertEqual(exit_code, 0)
        self.assertEqual(mock_stdout.getvalue().strip(), "test")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_execute_pipe_commands(self, mock_stdout):
        commands = ParsedInput(commands=[
            ParsedCommand("echo", ["line1\nline2\nline3"]),
            ParsedCommand("wc", [])
        ])
        exit_code = self.executor.execute(commands)
        self.assertEqual(exit_code, 0)
        self.assertEqual(mock_stdout.getvalue().strip(), "3 3 17")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_execute_with_error(self, mock_stdout):
        commands = ParsedInput(commands=[
            ParsedCommand("cat", ["nonexistent_file"]),
            ParsedCommand("wc", [])
        ])
        exit_code = self.executor.execute(commands)
        self.assertNotEqual(exit_code, 0)
