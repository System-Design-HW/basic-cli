import os
import tempfile
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
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.write(b"line1\nline2\nline3")
        self.temp_file.close()
        os.environ['TEST_VAR_PATH_TO_FILE'] = self.temp_file.name

    def tearDown(self):
        sys.stdout = sys.__stdout__
        os.unlink(self.temp_file.name)
        del os.environ['TEST_VAR']
        del os.environ['TEST_VAR_PATH_TO_FILE']

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

    @patch('builtins.input')
    def test_multiple_pipes_and_envvar(self, mock_input):
        mock_input.side_effect = [
            "cat $TEST_VAR_PATH_TO_FILE | cat | wc", 
            "exit"
        ]
        manager = CLIManager()
        manager.start()
        output = self.held_output.getvalue()
        self.assertIn("3 3 17", output)
        self.assertIn("Exit code: 0", output)
    
    @patch('builtins.input')
    def test_multiple_exit_in_multiple_pipes(self, mock_input):
        mock_input.side_effect = [
            "cat $TEST_VAR_PATH_TO_FILE | exit | wc", 
        ]
        manager = CLIManager()
        manager.start()
        output = self.held_output.getvalue()
        self.assertIn("`exit` received, closing...", output)
