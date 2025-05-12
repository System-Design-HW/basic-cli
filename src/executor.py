from typing import Optional
from src.commands import CommandRegistry
from src.parser import ParsedInput


class Executor:
    """Executes parsed commands using registered command implementations."""
    def __init__(self):
        """Initialize the executor with a command registry."""
        self.registry = CommandRegistry()

    def execute(self, commands: ParsedInput) -> int:
        """
        Execute a sequence of parsed commands and return the final exit code.

        Args:
            commands: ParsedInput object containing commands to execute

        Returns:
            int: Exit code from the last executed command
        """
        exit_code: int = 0
        previous_output: Optional[str] = None

        for command in commands.commands:
            cmd_obj = self.registry.get_command(command.command_name)

            exit_code, output = cmd_obj.execute(command=command, stdin=previous_output)

            previous_output = output

            if exit_code != 0:
                break

        if previous_output is not None:
            print(previous_output)

        return exit_code
