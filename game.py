from sgfrunner import BotAnalyzer
import argparse
import settings
from yaml import load

gameDict = {}
with open(settings.PATH_TO_CONFIG) as yaml_stream:
    yaml_data = load(yaml_stream)

CONFIG = yaml_data['config']
BOTS = yaml_data['bots']


def parse_cmd_line():
    parser = argparse.ArgumentParser(argument_default=None)

    # parser.add_argument("path_to_sgf", nargs='+',
    #                     help="List of SGF-files to analyze.")
    parser.add_argument('-b', '--bot', default=BOTS['default'],
                        dest='bot', help="Settings from config.yaml to use.")
    parser.add_argument('--no-vars', dest='no_variations',
                        action='store_true', help="Skip variations analysis.")

    return parser.parse_args()


cmd_args = parse_cmd_line()
game = BotAnalyzer(cmd_args.bot)
gameDict[1] = game
game.bot = game.create()
game.bot.start()
