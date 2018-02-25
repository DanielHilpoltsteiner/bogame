import argparse
import logging

import player_pb2
import report_lib


def run():
  parser = argparse.ArgumentParser()
  parser.add_argument('-i', '--input', type=str, required=True,
                      help='Output of parse.py')
  parser.add_argument('-v', '--verbose', action='store_true')
  args = parser.parse_args()

  if args.verbose:
    logging.basicConfig()
    logging.getLogger('bogame').setLevel(logging.DEBUG)

  player = player_pb2.Player()
  with open(args.input) as f:
    player.ParseFromString(f.read())

  for planet in player.planets:
    report = report_lib.generate_energy_report(player, planet)
    header = 'ENERGY REPORT FOR PLANET [{}]'.format(planet.name)
    print '-' * len(header)
    print header
    print '-' * len(header)
    print report


if __name__ == '__main__':
  run()
