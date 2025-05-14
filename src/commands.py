import os
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Type
from src.parser import ParsedCommand


class Command(ABC):
    """Abstract base class defining the command execution interface."""

    @abstractmethod
    def execute(self, command: ParsedCommand, current_dir: str = None) -> int:
        """
        Execute the command with provided arguments.

        Args:
            command: ParsedCommand object containing command name and arguments
            current_dir: Current working directory for command execution

        Returns:
            int: Exit status code (0 for success, non-zero for errors)
        """
        pass


class CatCommand(Command):
    """Implementation of 'cat' command to display file content."""

    def execute(self, command: ParsedCommand, current_dir: str = None) -> int:
        """
        Execute cat command to print file contents.

        Handles:
        - File not found errors
        - Permission errors
        - Generic I/O errors
        """
        try:
            filepath: str = command.args[0]
            with open(filepath, 'r') as f:
                print(f.read(), end='')
            return 0
        except Exception as e:
            print(f"Error `cat`: {e}")
            return 1


class EchoCommand(Command):
    """Implementation of 'echo' command to print arguments."""

    def execute(self, command: ParsedCommand, current_dir: str = None) -> int:
        """Print all arguments joined by spaces."""
        print(' '.join(command.args))
        return 0


class WcCommand(Command):
    """Implementation of 'wc' command for word count statistics."""

    def execute(self, command: ParsedCommand, current_dir: str = None) -> int:
        """
        Calculate and print:
        - Line count
        - Word count
        - Byte size
        for specified file.
        """
        try:
            # Open file
            filepath: str = command.args[0]
            with open(filepath, 'r') as f:
                content = f.read()

            # Calculate metrics
            lines: int = len(content.split('\n'))
            words: int = len(content.split())
            bytes: int = os.path.getsize(filepath)

            print(f"{lines} {words} {bytes}")
            return 0
        except Exception as e:
            print(f"Error `wc`: {e}")
            return 1


class PwdCommand(Command):
    """Implementation of 'pwd' command to print working directory."""

    def execute(self, command: ParsedCommand, current_dir: str = None) -> int:
        """Print current working directory using OS API."""
        if current_dir:
            print(current_dir)
        else:
            print(os.getcwd())
        return 0


class ExitCommandException(Exception):
    """Special exception to signal shell termination."""


class ExitCommand(Command):
    """Implementation of 'exit' command to terminate the shell."""

    def execute(self, command: ParsedCommand, current_dir: str = None) -> int:
        """Raise termination exception to break execution loop."""
        raise ExitCommandException


class DefaultCommand(Command):
    """Fallback command executor for external system commands."""

    def execute(self, command: ParsedCommand, current_dir: str = None) -> int:
        """
        Execute external command using subprocess.

        Handles:
        - Command not found errors
        - Non-zero exit codes from child processes
        - Output capturing and display
        """
        try:
            cwd = current_dir if current_dir else os.getcwd()
            result = subprocess.run(
                [command.command_name] + command.args,
                check=True, capture_output=True, text=True,
                cwd=cwd
            )
            print(result.stdout)
            return result.returncode
        except FileNotFoundError:
            print(f"{command.command_name}: command not found")
            return 1
        except subprocess.CalledProcessError as e:
            print(f"error in execution: {command.command_name}: {e.stderr}")
            return e.returncode


class CdCommand(Command):
    """Implementation of 'cd' command to change the current directory."""

    def execute(self, command: ParsedCommand, current_dir: str = None) -> int:
        """
        Change the current working directory.
        
        Args:
            command: ParsedCommand object containing command name and arguments
            current_dir: Current working directory
            
        Returns:
            int: Exit status code (0 for success, non-zero for errors)
        """
        try:
            if not command.args:
                target_dir = os.path.expanduser("~")
            else:
                target_dir = command.args[0]
                
            if current_dir and not os.path.isabs(target_dir):
                target_dir = os.path.normpath(os.path.join(current_dir, target_dir))
                
            if not os.path.isdir(target_dir):
                print(f"cd: {target_dir}: No such directory")
                return 1
                
            if hasattr(self, 'manager'):
                self.manager.current_dir = target_dir
                
            os.chdir(target_dir)
            return 0
        except Exception as e:
            print(f"cd: {e}")
            return 1


class LsCommand(Command):
    """Implementation of 'ls' command to list directory contents."""

    def execute(self, command: ParsedCommand, current_dir: str = None) -> int:
        """
        List contents of a directory.
        
        Args:
            command: ParsedCommand object containing command name and arguments
            current_dir: Current working directory
            
        Returns:
            int: Exit status code (0 for success, non-zero for errors)
        """
        try:
            if not command.args:
                target_dir = current_dir if current_dir else os.getcwd()
            else:
                target_dir = command.args[0]
                if current_dir and not os.path.isabs(target_dir):
                    target_dir = os.path.normpath(os.path.join(current_dir, target_dir))
            
            if not os.path.isdir(target_dir):
                print(f"ls: {target_dir}: No such directory")
                return 1

            entries = os.listdir(target_dir)
            for entry in sorted(entries):
                print(entry)
                
            return 0
        except Exception as e:
            print(f"ls: {e}")
            return 1


class CommandRegistry:
    """Registry mapping command names to their implementations."""

    _commands: Dict[str, Type[Command]] = {
        'cat': CatCommand,
        'echo': EchoCommand,
        'wc': WcCommand,
        'pwd': PwdCommand,
        'exit': ExitCommand,
        'cd': CdCommand,
        'ls': LsCommand
    }

    def get_command(self, name: str) -> Command:
        """
        Get command implementation for specified name.

        Returns:
            Command: Concrete command implementation
                     DefaultCommand if name not registered
        """
        return self._commands.get(name, DefaultCommand)()
