import argparse
import re
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, List, Type
from src.parser import ParsedCommand
import os
import sys
from typing import Optional


class Command(ABC):
    """Abstract base class defining the command execution interface."""

    @abstractmethod
    def execute(self, command: ParsedCommand, stdin: Optional[str] = None) -> tuple[int, Optional[str]]:
        """
        Execute the command with provided arguments.

        Args:
            command: ParsedCommand object containing command name and arguments
            stdin: Optional input from previous command in pipe

        Returns:
            tuple: (exit status code, output)
                   Exit status code (0 for success, non-zero for errors)
                   Output string or None if output was already printed
        """
        pass


class CatCommand(Command):
    """Implementation of 'cat' command to display file content."""

    def execute(self, command: ParsedCommand, stdin: Optional[str] = None) -> tuple[int, Optional[str]]:
        """
        Execute cat command to print file contents.

        Handles:
        - File not found errors
        - Permission errors
        - Generic I/O errors
        - Reading from stdin if no file specified
        """
        try:
            if not command.args and stdin is not None:
                return (0, stdin)
            elif not command.args:
                content = sys.stdin.read()
                return (0, content)

            output = []
            for filepath in command.args:
                with open(filepath, 'r') as f:
                    output.append(f.read())
            return (0, ''.join(output))
        except Exception as e:
            print(f"Error `cat`: {e}", file=sys.stderr)
            return (1, None)


class EchoCommand(Command):
    """Implementation of 'echo' command to print arguments."""

    def execute(self, command: ParsedCommand, stdin: Optional[str] = None) -> tuple[int, Optional[str]]:
        """Print all arguments joined by spaces."""
        output = ' '.join(command.args)
        if stdin is not None:
            output = stdin + output
        return (0, output)


class WcCommand(Command):
    """Implementation of 'wc' command for word count statistics."""

    def execute(self, command: ParsedCommand, stdin: Optional[str] = None) -> tuple[int, Optional[str]]:
        """
        Calculate and print:
        - Line count
        - Word count
        - Byte size
        for specified file or stdin.
        """
        try:
            content = None
            if command.args:
                # Read from file
                filepath = command.args[0]
                with open(filepath, 'r') as f:
                    content = f.read()
                bytes = os.path.getsize(filepath)
            elif stdin is not None:
                content = stdin
                bytes = len(content.encode('utf-8'))
            else:
                content = sys.stdin.read()
                bytes = len(content.encode('utf-8'))

            if content is None:
                raise ValueError("No input source specified")

            lines = len(content.split('\n'))
            words = len(content.split())

            output = f"{lines} {words} {bytes}"
            return (0, output)
        except Exception as e:
            print(f"Error `wc`: {e}", file=sys.stderr)
            return (1, None)


class PwdCommand(Command):
    """Implementation of 'pwd' command to print working directory."""

    def execute(self, command: ParsedCommand, stdin: Optional[str] = None) -> tuple[int, Optional[str]]:
        """Print current working directory using OS API."""
        return (0, os.getcwd())


class ExitCommandException(Exception):
    """Special exception to signal shell termination."""


class ExitCommand(Command):
    """Implementation of 'exit' command to terminate the shell."""

    def execute(self, command: ParsedCommand, stdin: Optional[str] = None) -> tuple[int, Optional[str]]:
        """Raise termination exception to break execution loop."""
        raise ExitCommandException


class GrepCommand(Command):
    def execute(self, command: ParsedCommand, stdin: Optional[str] = None) -> tuple[int, Optional[str]]:
        try:
            args = self._parse_args(command.args)
        except ValueError as e:
            print(f"grep error: {e}", file=sys.stderr)
            return (1, None)

        pattern = self._build_pattern(args.pattern, args.word, args.ignore_case)
        lines = self._read_input(command, stdin)
        result = self._process_lines(lines, pattern, args.after_context)

        return (0, '\n'.join(result) if result else None)

    def _parse_args(self, args: List[str]) -> argparse.Namespace:
        parser = argparse.ArgumentParser(prog='grep', add_help=False)
        parser.add_argument('-w', '--word', action='store_true', help='match whole words only')
        parser.add_argument('-i', '--ignore-case', action='store_true', help='case insensitive search')
        parser.add_argument('-A', '--after-context', type=int, default=0, help='print N lines after match')
        parser.add_argument('pattern', help='search pattern')
        parser.add_argument('file', nargs='?', help='input file')

        try:
            return parser.parse_args(args)
        except argparse.ArgumentError as e:
            raise ValueError(str(e))

    def _build_pattern(self, pattern: str, whole_word: bool, ignore_case: bool) -> re.Pattern:
        regex = pattern
        if whole_word:
            regex = r'\b' + re.escape(pattern) + r'\b'
        flags = re.IGNORECASE if ignore_case else 0
        return re.compile(regex, flags)

    def _read_input(self, command: ParsedCommand, stdin: Optional[str]) -> List[str]:
        args = self._parse_args(command.args)
        if args.file:
            with open(args.file, 'r') as f:
                return f.read().splitlines()
        elif stdin:
            return stdin.splitlines()
        else:
            return sys.stdin.read().splitlines()

    def _process_lines(self, lines: List[str], pattern: re.Pattern, after_context: int) -> List[str]:
        result = []
        remaining_context = 0

        for i, line in enumerate(lines):
            if pattern.search(line):
                result.append(line)
                remaining_context = after_context
            elif remaining_context > 0:
                result.append(line)
                remaining_context -= 1

        return result


class DefaultCommand(Command):
    """Fallback command executor for external system commands."""

    def execute(self, command: ParsedCommand, stdin: Optional[str] = None) -> tuple[int, Optional[str]]:
        """
        Execute external command using subprocess.

        Handles:
        - Command not found errors
        - Non-zero exit codes from child processes
        - Output capturing and display
        - Piping input from previous command
        """
        try:
            input_data = stdin.encode('utf-8') if stdin else None

            result = subprocess.run(
                [command.command_name] + command.args,
                input=input_data,
                check=False,
                capture_output=True,
                text=False
            )

            stdout = result.stdout.decode('utf-8').rstrip('\n')
            stderr = result.stderr.decode('utf-8').rstrip('\n')

            if stderr:
                print(stderr, file=sys.stderr)

            return (result.returncode, stdout)
        except FileNotFoundError:
            print(f"{command.command_name}: command not found", file=sys.stderr)
            return (1, None)


class CommandRegistry:
    """Registry mapping command names to their implementations."""

    _commands: Dict[str, Type[Command]] = {
        'cat': CatCommand,
        'echo': EchoCommand,
        'wc': WcCommand,
        'pwd': PwdCommand,
        'exit': ExitCommand,
        'grep': GrepCommand
    }

    def get_command(self, name: str) -> Command:
        """
        Get command implementation for specified name.

        Returns:
            Command: Concrete command implementation
                     DefaultCommand if name not registered
        """
        return self._commands.get(name, DefaultCommand)()
