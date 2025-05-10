import shlex
from typing import List
import os
import re


class ParsedCommand:
    """Class representing a parsed command.

    Attributes:
        command_name (str): The name of the command.
        args (List[str]): List of command arguments.
    """
    def __init__(self, command_name: str, args: List[str]):
        self.command_name = command_name
        self.args = args


class ParsedInput:
    """Class representing parsed user input.

    Attributes:
        commands (List[ParsedCommand]): List of parsed commands.
        substitutions (Dict[str, str]): Dictionary of variable substitutions.
    """
    def __init__(self, commands: List[ParsedCommand]):
        self.commands = commands


class ParseError(Exception):
    """Custom exception for command parsing errors"""
    pass


class Parser:
    """Class for parsing user input into a structured format."""

    def _parse_command(self, input: str) -> ParsedCommand:
        """Internal method to parse a string into a command and arguments.

        Uses shlex.split to properly handle quotes and spaces.

        Args:
            input (str): User input string (e.g., "cmd 'arg 1' arg2").

        Returns:
            ParsedCommand: Object containing the command and its arguments.
        """
        args: List[str] = shlex.split(input)

        if len(args) == 0:
            raise ParseError("Empty command")

        command_name: str = args.pop(0)
        return ParsedCommand(command_name=command_name, args=args)

    def parse(self, input: str) -> ParsedInput:
        """Main method to parse user input.

        Args:
            input: Input string to parse.

        Returns:
            ParsedInput: Object containing parsed commands.

        Raises:
            ParseError: If input is empty or cannot be parsed
        """
        if not input.strip():
            raise ParseError("Empty input")

        input = self._process_substitutions(input)

        commands = []
        for cmd_str in input.split('|'):
            cmd_str = cmd_str.strip()
            if cmd_str:
                commands.append(self._parse_command(cmd_str))

        return ParsedInput(commands=commands)

    def _process_substitutions(self, input: str) -> str:
        """Process variable substitutions in the input string.

        Args:
            input: Original input string

        Returns:
            str: String with substitutions applied
        """
        def replace_var(match):
            var_name = match.group(1)
            return os.getenv(var_name, '')

        input = re.sub(r'\$\{(\w+)\}', replace_var, input)
        input = re.sub(r'\$(\w+)', replace_var, input)

        return input
