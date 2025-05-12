import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Type
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
        'exit': ExitCommand
    }

    def get_command(self, name: str) -> Command:
        """
        Get command implementation for specified name.

        Returns:
            Command: Concrete command implementation
                     DefaultCommand if name not registered
        """
        return self._commands.get(name, DefaultCommand)()
