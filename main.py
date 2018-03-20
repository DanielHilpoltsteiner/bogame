import argparse
import sys

from PyQt5.QtWidgets import QApplication

from bogame.core.player_pb2 import Player
from bogame.gui.dashboard import DashboardWindow
from bogame.gui.login import LoginWindow

if __name__ == '__main__':
  app = QApplication(sys.argv)

  # Skip login if file provided from command line.
  arg_parser = argparse.ArgumentParser()
  arg_parser.add_argument('-i', '--input', type=str, help='Saved player info')
  args = arg_parser.parse_args()
  if args.input:
    player = Player()
    with open(args.input, 'rb') as f:
      player.ParseFromString(f.read())
    dashboard = DashboardWindow()
    dashboard.display(player)
  else:
    login = LoginWindow()
    dashboard = DashboardWindow()
    login.finished.connect(dashboard.display)

  app.exec_()
  app.deleteLater()
