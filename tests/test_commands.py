import subprocess
import unittest
import os
import tempfile
import io
from unittest.mock import patch
from src.commands import (
    EchoCommand, CatCommand, WcCommand, PwdCommand,
    ExitCommand, DefaultCommand, ExitCommandException
)
from src.parser import ParsedCommand


class TestCommands(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.write(b"line1\nline2\nline3")
        self.temp_file.close()
        os.environ['TEST_VAR'] = 'test_value'

    def tearDown(self):
        os.unlink(self.temp_file.name)
        del os.environ['TEST_VAR']

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_echo_command(self, mock_stdout):
        cmd = EchoCommand()
        exit_code, output = cmd.execute(ParsedCommand("echo", ["test"]))
        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "test")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cat_command(self, mock_stdout):
        cmd = CatCommand()
        exit_code, output = cmd.execute(ParsedCommand("cat", [self.temp_file.name]))
        self.assertEqual(exit_code, 0)
        self.assertIn("line1", output)
        self.assertIn("line2", output)
        self.assertIn("line3", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cat_command_with_stdin(self, mock_stdout):
        cmd = CatCommand()
        exit_code, output = cmd.execute(
            ParsedCommand("cat", []), 
            stdin="piped input"
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "piped input")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_wc_command(self, mock_stdout):
        cmd = WcCommand()
        exit_code, output = cmd.execute(ParsedCommand("wc", [self.temp_file.name]))
        self.assertEqual(exit_code, 0)
        expected_lines = 3
        expected_words = 3
        expected_bytes = 3 * 5 + 2 
        expected = f"{expected_lines} {expected_words} {expected_bytes}"
        self.assertEqual(output, expected)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_wc_command_with_stdin(self, mock_stdout):
        cmd = WcCommand()
        exit_code, output = cmd.execute(
            ParsedCommand("wc", []), 
            stdin="line1\nline2\nline3"
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "3 3 17")
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_pwd_command(self, mock_stdout):
        cmd = PwdCommand()
        exit_code, output = cmd.execute(ParsedCommand("pwd", []))
        self.assertEqual(exit_code, 0)
        self.assertEqual(output, os.getcwd())

    def test_exit_command(self):
        cmd = ExitCommand()
        with self.assertRaises(ExitCommandException):
            cmd.execute(ParsedCommand("exit", []))

    @patch('subprocess.run')
    def test_default_command(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=['head', '-n', '1', self.temp_file.name],
            returncode=0,
            stdout=b'line1\n',
            stderr=b''
        )
        cmd = DefaultCommand()
        exit_code, output = cmd.execute(
            ParsedCommand("head", [self.temp_file.name, "-n", "1"])
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "line1")

    @patch('subprocess.run')
    def test_default_command_with_stdin(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=['grep', 'line2'],
            returncode=0,
            stdout=b'line2\n',
            stderr=b''
        )
        cmd = DefaultCommand()
        exit_code, output = cmd.execute(
            ParsedCommand("grep", ["line2"]),
            stdin="line1\nline2\nline3"
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "line2")
