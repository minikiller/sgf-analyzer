import hashlib
from subprocess import Popen, PIPE
from time import sleep

from log import logger
from readerthread import start_reader_thread
from utils import convert_position


class GTPConsole:
    def __init__(self, executable, arguments,
                 board_size=19, komi=6.5, handicap=0, time_per_move=60):
        self._history = []

        self.process = None
        self.stdout_thread = None
        self.stderr_thread = None

        self.executable = executable
        self.arguments = arguments.split()

        self.board_size = board_size
        self.komi = komi
        self.handicap = handicap
        self.time_per_move = time_per_move

    def _history_hash(self) -> str:
        """Returns MD5 hash for current history."""
        history_hash = hashlib.md5()

        for command in self._history:
            history_hash.update(bytes(command, 'utf-8'))

        return history_hash.hexdigest()

    def add_move_to_history(self, color: str, pos: str):
        """ Convert given SGF coordinates to GTP console command"""
        move = convert_position(self.board_size, pos)
        command = f"play {color} {move}"
        self._history.append(command)

    def pop_move_from_history(self, count=1):
        """ Removes given number of last commands from history"""
        for i in range(count):
            self._history.pop()

    def _clean_history(self):
        self._history.clear()

    def whose_turn(self) -> str:
        """ Return color of next move, based on number of handicap stones and moves."""
        if len(self._history) == 0:
            return "white" if self.handicap else "black"
        else:
            return "black" if "white" in self._history[-1] else "white"

    def reset(self):
        self._clean_history()
        self.stop()
        self.start()

    def _drain_output(self):
        """ Drains all remaining stdout and stderr contents"""
        return self.stdout_thread.read_all_lines(), self.stderr_thread.read_all_lines()

    def _send_command(self, cmd, timeout=100, drain=True, no_wait=False):
        """Send command to GTP console and drains stdout/stderr"""
        if isinstance(cmd, list):
            commands_count = len(cmd)
            command = '\n'.join(cmd)
        else:
            commands_count = 1
            command = cmd

        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

        if no_wait:
            return None

        tries = 0
        success_count = 0
        while tries <= timeout:
            # Loop until reach given number of success
            while True:
                s = self.stdout_thread.readline()

                # Break loop, sleep and wait for more
                if s == "":
                    break

                # GTP prints a line starting with "=" upon success.
                if '=' in s:
                    success_count += 1
                    if success_count >= commands_count:
                        if drain:
                            self._drain_output()
                        return

            tries += 1
            sleep(0.1)

        logger.warning(f"Failed to send command: {command}")

    def start(self):
        logger.info("Starting GTP...")

        self.process = Popen([self.executable] + self.arguments,
                             stdout=PIPE,
                             stdin=PIPE,
                             stderr=PIPE,
                             universal_newlines=True)
        sleep(2)
        self.stdout_thread = start_reader_thread(self.process.stdout)
        self.stderr_thread = start_reader_thread(self.process.stderr)

        self._send_command(f'boardsize {self.board_size}')
        self._send_command(f'komi {self.komi}')
        self._send_command(f'time_settings 0 {self.time_per_move} 1')
        logger.info("GTP started successfully.")

    def stop(self):
        """Stop GTP console"""
        logger.info("Stopping GTP...")

        if self.process is None:
            return

        self.stdout_thread.stop()
        self.stderr_thread.stop()
        self._send_command('quit')

        logger.info("GTP stopped successfully...")

    def showboard(self):
        """Show board"""
        self._send_command("showboard", drain=False)
        (so, se) = self._drain_output()
        return "".join(se)

    def go_to_position(self):
        """Send all moves from history to GTP console"""
        self._send_command('clear_board')
        self._send_command(self._history)
