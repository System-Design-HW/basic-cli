import os
from typing import Optional
from src.commands import ExitCommandException
from src.executor import Executor
from src.parser import Parser


class CLIManager:
    """Main controller class for CLI session management."""

    def __init__(self):
        """Initialize CLI components and state."""
        self.parser = Parser()		# Command input parser
        self.executor = Executor()  # Command execution handler
        self.is_running = False		# Session activity flag
        self.current_dir = os.getcwd()  # Track current working directory

    def start(self):
        """Start the REPL (Read-Eval-Print Loop) session."""
        self.is_running = True
        while self.is_running:
            try:
                # Get user input
                input = self._get_input()
                if not input:
                    continue

                # Process command and display exit code
                exit_code = self._process_command(input)
                print(f"Exit code: {exit_code}")
            except ExitCommandException:
                print("`exit` received, closing...\n")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
            except KeyboardInterrupt:
                print("\nInterrupt received, closing...\n")
                break

    def _get_input(self) -> Optional[str]:
        """
        Safely get user input with error handling.

        Returns:
            Optional[str]: Cleaned input string or None for EOF
        """
        try:
            return input("> ").strip()
        except EOFError:
            self._stop()
            return None

    def _process_command(self, input: str) -> int:
        """
        Execute full command processing pipeline.

        Args:
            input_str: Raw user input string

        Returns:
            int: Final exit code from command execution
        """
        parsed_input = self.parser.parse(input)
        if not parsed_input.commands:
            return 0  # Return success for empty input

        exit_code = self.executor.execute(parsed_input, self.current_dir)
        
        if parsed_input.commands[0].command_name == 'cd' and exit_code == 0:
            self.current_dir = os.getcwd()
            
        return exit_code

    def _stop(self):
        """Gracefully terminate CLI session."""
        self.is_running = False
        print("\nSession terminated.")
