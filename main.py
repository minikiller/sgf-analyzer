from bot_engines import LeelaZeroCLI
from sgfanalyze import BotAnalyzer
import argparse
import settings
import os
from yaml import load
from utils import convert_position, parse_position

def parse_cmd_line():
    parser = argparse.ArgumentParser(argument_default=None)

    parser.add_argument("path_to_sgf", nargs='+',
                        help="List of SGF-files to analyze.")
    parser.add_argument('-b', '--bot', default=BOTS['default'],
                        dest='bot', help="Settings from config.yaml to use.")
    parser.add_argument('--no-vars', dest='no_variations',
                        action='store_true', help="Skip variations analysis.")

    return parser.parse_args()

def process_path(path_string):
    games = []
    for path in path_string:
        if os.path.isdir(path):
            for file in os.listdir(path):
                path_to_file = os.path.join(path, file)
                if os.path.splitext(path_to_file)[1] == '.sgf':
                    games.append(path_to_file)
        elif os.path.exists(path):
            games.append(path)

    return games

with open(settings.PATH_TO_CONFIG) as yaml_stream:
    yaml_data = load(yaml_stream)

CONFIG = yaml_data['config']
BOTS = yaml_data['bots']
cmd_args = parse_cmd_line()

game_list = process_path(cmd_args.path_to_sgf)


queue = []
for game in game_list:
    queue.append(BotAnalyzer(game, cmd_args.bot))

for game in queue:
    game.bot=game.create()
    game.bot.start()
    stdout, stderr = game.bot.genmove()

    # Drain and parse Leela stdout & stderr
    stats, move_list = game.bot.parse_analysis(stdout, stderr)

    if stats.get('winrate') and move_list:
        best_move = convert_position(game.board_size, move_list[0]['pos'])

    print(best_move)
    game.bot.stop()

 
