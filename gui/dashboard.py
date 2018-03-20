"""Dashboard GUI."""
from PyQt5.QtCore import (
    pyqtSlot,
)
from PyQt5.QtWidgets import (
    QDesktopWidget,
    QErrorMessage,
    QFileDialog,
    QFrame,
    QMainWindow,
    QPlainTextEdit,
    QTabWidget,
    QVBoxLayout,
)

from bogame.analysis import energy_analysis
from bogame.core.player_pb2 import Player
from bogame.gui import dashboard_energy


class DashboardWindow(QMainWindow):

  def __init__(self):
    super().__init__()
    self._player = None

  def center(self):
    resolution = QDesktopWidget().screenGeometry()
    self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
              (resolution.height() / 2) - (self.frameSize().height() / 2))

  def setup_menu(self):
    menu_file = self.menuBar().addMenu('File')
    action_save_player = menu_file.addAction('Save player...')
    action_save_player.triggered.connect(self._save_player)

  @pyqtSlot()
  def _save_player(self):
    filename = QFileDialog.getSaveFileName(
        self, 'Save player info', '', 'Bogame file (*.bog)')
    if filename and filename[0]:
      try:
        with open(filename[0], 'wb') as f:
          f.write(self._player.SerializeToString())
        self.statusBar().showMessage(
            'Saved player info to ' + filename[0], 3000)
      except Exception as e:
        error_dialog = QErrorMessage(self)
        error_dialog.showMessage('Failed to save player info: {}'.format(e))

  @pyqtSlot(Player)
  def display(self, player):
    self._player = player
    self._dashboard = Dashboard(player, self)
    self.setCentralWidget(self._dashboard)
    self.setWindowTitle('Bogame')
    self.setMinimumWidth(800)
    self.setMinimumHeight(600)
    self.center()
    self.statusBar().showMessage('Welcome, {}'.format(player.identity.name))
    self.setup_menu()
    self.show()


class Dashboard(QFrame):

  def __init__(self, player, parent):
    super().__init__(parent)
    self._player = player
    self.init_ui()

  def init_ui(self):
    # Tab Energy.
    energy_reports = []
    for planet in self._player.planets:
      report = energy_analysis.generate_energy_report(self._player, planet)
      energy_reports.append((planet, report))
      if planet.HasField('moon'):
        report = energy_analysis.generate_energy_report(
            self._player, planet.moon)
        energy_reports.append((planet.moon, report))
    self._tab_energy = dashboard_energy.EnergyDashboard(energy_reports, self)

    # Tab Details.
    self._tab_details = QPlainTextEdit(self)
    self._tab_details.setReadOnly(True)
    self._tab_details.setPlainText(str(self._player))

    # Tabs.
    self._tabs = QTabWidget(self)
    self._tabs.addTab(self._tab_energy, 'Energy')
    self._tabs.addTab(self._tab_details, 'Details')

    # Layout.
    layout = QVBoxLayout()
    layout.addWidget(self._tabs)
    self.setLayout(layout)
