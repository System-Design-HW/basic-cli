import os
import unittest
from unittest.mock import patch
from io import StringIO
import sys
from src.manager import CLIManager


class TestCLIManager(unittest.TestCase):
    def setUp(self):
        self.held_output = StringIO()
        sys.stdout = self.held_output
        os.environ['TEST_VAR'] = 'test_value'

    def tearDown(self):
        sys.stdout = sys.__stdout__
        del os.environ['TEST_VAR']

    @patch('builtins.input')
    def test_session_flow(self, mock_input):
        mock_input.side_effect = ["echo test", "exit"]
        manager = CLIManager()
        manager.start()
        output = self.held_output.getvalue()
        self.assertIn("test", output)
        self.assertIn("Exit code: 0", output)
        self.assertIn("`exit` received, closing...", output)

    @patch('builtins.input')
    def test_pipe_commands(self, mock_input):
        mock_input.side_effect = ["echo line1 line2 line3 | wc", "exit"]
        manager = CLIManager()
        manager.start()
        output = self.held_output.getvalue()
        self.assertIn("1 3 17", output)  # 1 line, 3 words, 17 bytes
        self.assertIn("Exit code: 0", output)

    @patch('builtins.input')
    def test_variable_substitution(self, mock_input):
        mock_input.side_effect = ["echo $TEST_VAR", "exit"]
        manager = CLIManager()
        manager.start()
        output = self.held_output.getvalue()
        self.assertIn("test_value", output)
        self.assertIn("Exit code: 0", output)

    @patch('builtins.input')
    def test_multiple_pipes(self, mock_input):
        mock_input.side_effect = [
            "echo line1 line2 line3 | cat | wc", 
            "exit"
        ]
        manager = CLIManager()
        manager.start()
        output = self.held_output.getvalue()
        self.assertIn("1 3 17", output)
        self.assertIn("Exit code: 0", output)