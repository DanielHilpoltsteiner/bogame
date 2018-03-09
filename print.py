import argparse

import player_pb2


def run():
  parser = argparse.ArgumentParser()
  parser.add_argument('-i', '--input', type=str, required=True,
                      help='Output of parse.py')
  args = parser.parse_args()

  player = player_pb2.Player()
  with open(args.input, 'rb') as f:
    player.ParseFromString(f.read())
  print(player)


if __name__ == '__main__':
  run()
