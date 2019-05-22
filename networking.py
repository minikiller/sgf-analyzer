from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from leelazero import LeelaZero
from yaml import load
import settings

with open(settings.PATH_TO_CONFIG) as yaml_stream:
    yaml_data = load(yaml_stream)


def get_leela_zero():
    kwargs = {'board_size': 19,
              'komi': 6.5,
              'handicap': 0,
              'time_per_move': 1}

    kwargs.update(yaml_data['bots']['leela-zero'])
    print(kwargs)
    return LeelaZero(**kwargs)


bot = get_leela_zero()
bot.start()


# Create custom HTTPRequestHandler class
class BadukHTTPRequestHandler(BaseHTTPRequestHandler):
    # handle GET command
    def do_GET(self):
        try:
            move = self.path[1:]
            print(move)
            if move == 'new':
                bot.reset()

            elif 1 < len(move) < 4:
                print('Move to play:', move)
                ai_move = bot.genmove_and_play(move)
                print('Bot moves:', ai_move)
            board = bot.showboard()
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(board.encode('utf8'))
            return

        except:
            self.send_error(404, 'Cannot play this move')


def run():
    print('http server is starting...')

    # ip and port of servr
    # by default http server port is 80
    server_address = ('127.0.0.1', 80)
    httpd = HTTPServer(server_address, BadukHTTPRequestHandler)
    print('Socket', httpd.socket)
    print('Address', server_address)
    print('http server is running...')
    httpd.serve_forever()


if __name__ == '__main__':
    run()
