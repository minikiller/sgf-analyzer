import re
from time import sleep

from gtp import GTPConsole
from log import logger
from utils import convert_position, parse_position

UPDATE_REGEX = r'Playouts: ([0-9]+), Win: ([0-9]+\.[0-9]+)\%, PV:(( [A-Z][0-9]+)+)'

STATUS_REGEX = r'NN eval=([0-9]+\.[0-9]+)'

MOVE_REGEX = r'\s*([A-Z][0-9]+) -> +([0-9]+) ' \
             r'\(V: +([0-9]+\.[0-9]+)\%\) .*' \
             r'\(N: +([0-9]+\.[0-9]+)\%\) ' \
             r'PV: (.*)$'

STATS_REGEX = r'([0-9]+) visits, ' \
              r'([0-9]+) nodes(?:, ([0-9]+) playouts)(?:, ([0-9]+) n/s)'

FINISHED_REGEX = r'= ([A-Z][0-9]+|resign|pass)'

BEST_REGEX = r'([0-9]+) visits, ' \
             r'score (\-? ?[0-9]+\.[0-9]+)\% \(from \-? ?[0-9]+\.[0-9]+\%\) ' \
             r'PV: (.*)'


def str_to_percent(value: str):
    return 0.01 * float(value.strip())


class LeelaZero(GTPConsole):
    """ Command Line Interface designed to work with GTP protocol."""

    def analyze(self):
        """Analyze current position with given seconds per search."""
        stdout, stderr = self._generate_move()

        # Drain and parse Leela stdout & stderr
        stats, move_list = self._parse_output(stdout, stderr)

        if stats.get('winrate') and move_list:
            best_move = convert_position(self.board_size, move_list[0]['pos'])
            winrate = (stats['winrate'] * 100)
            visits = stats['visits']
            pv = " ".join([convert_position(self.board_size, m) for m in move_list[0]['pv']])
            logger.debug(f"Suggested: %s (winrate %.2f%%, %d visits). Perfect sequence: %s",
                         best_move, winrate, visits, pv)
        else:
            chosen_move = convert_position(self.board_size, stats['chosen'])
            logger.debug(f"Chosen move: %s", chosen_move)

        return stats, move_list

    def _generate_move(self):
        self._send_command(f'time_left black {self.time_per_move:d} 1')
        self._send_command(f'time_left white {self.time_per_move:d} 1')
        self._send_command(f"genmove {self.whose_turn()}\n", no_wait=True)

        updated = 0
        stdout = []
        stderr = []

        while updated < self.time_per_move * 2:
            out, err = self._drain_output()
            stdout.extend(out)
            stderr.extend(err)

            self._parse_status_update("".join(err))

            if out:
                break

            updated += 1
            sleep(1)

        # Confirm generated move with new line
        self._send_command("", no_wait=True)

        # Drain the rest of output
        out, err = self._drain_output()
        stdout.extend(out)
        stderr.extend(err)

        return stdout, stderr

    def _parse_status_update(self, message):
        m = re.match(UPDATE_REGEX, message)

        if m is not None:
            visits = int(m.group(1))
            winrate = self._get_winrate(str_to_percent(m.group(2)))
            pv = ' '.join([str(move) for move in m.group(3).split()])
            logger.debug("Visited %s positions, black winrate %.2f%%, PV: %s", visits,
                         winrate * 100, pv)

    def _parse_output(self, stdout, stderr):
        """Parse stdout & stderr."""
        logger.debug(f"GTP stdout:\n%s", ''.join(stdout))
        logger.debug(f"GTP stderr:\n%s", ''.join(stderr))

        stats = {}
        move_list = []

        for line in stderr:
            line = line.strip()
            stats = self._parse_status(line)
            move_list = self._parse_move(move_list, line)
            stats = self._parse_stats(stats, line)

        stats['best'] = move_list[0]['pos']
        stats['winrate'] = move_list[0]['winrate']

        stats = self._parse_finished(stats, stdout)

        required_keys = ['best', 'winrate', 'visits']

        # Check for missed data
        for k in required_keys:
            if k not in stats:
                logger.warning("Analysis stats missing %s data", k)

        # In the case where Leela resigns, just replace with the move Leela did think was best
        if stats['chosen'] == "resign":
            stats['chosen'] = stats['best']

        return stats, move_list

    def _parse_status(self, line):
        # Find status string
        m = re.match(STATUS_REGEX, line)
        if m is not None:
            return {'winrate': self._get_winrate(float(m.group(1)))}
        return {}

    def _parse_move(self, move_list, line):
        m = re.match(MOVE_REGEX, line)
        if m is not None:
            pos = parse_position(self.board_size, m.group(1))
            visits = int(m.group(2))
            winrate = self._get_winrate(str_to_percent(m.group(3)))
            policy_prob = str_to_percent(m.group(4))
            pv = [parse_position(self.board_size, p) for p in m.group(5).split()]

            info = {
                'pos': pos,
                'visits': visits,
                'winrate': winrate,
                'policy_prob': policy_prob,
                'pv': pv,
                'color': self.whose_turn()
            }
            move_list.append(info)
        return move_list

    def _parse_stats(self, stats, line):
        m = re.match(STATS_REGEX, line)
        if m is not None:
            stats['visits'] = int(m.group(1))
        return stats

    def _parse_finished(self, stats, stdout):
        m = re.search(FINISHED_REGEX, "".join(stdout))
        if m is not None:
            stats['chosen'] = "resign" if m.group(1) == "resign" else parse_position(
                self.board_size, m.group(1))
        return stats

    def _get_winrate(self, wr):
        return (1.0 - wr) if self.whose_turn() == "white" else wr
