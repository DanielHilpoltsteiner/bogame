import configparser
import re
import sys
import threading
import time

from PyQt5.QtWidgets import (
    qApp,
    QApplication,
    QComboBox,
    QDesktopWidget,
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressDialog,
    QPushButton,
)
from PyQt5.QtCore import (
    pyqtSignal,
    pyqtSlot,
    QObject,
    QRegExp,
    Qt,
    QThread,
)
from PyQt5.QtGui import (
    QIntValidator,
    QRegExpValidator,
    QValidator,
)

from parser import Parser

_COUNTRIES = {
    u'Argentina': 'ar',
    u'Brasil': 'br',
    u'Česká Republika': 'cz',
    u'Danmark': 'dk',
    u'Deutschland': 'de',
    u'España': 'es',
    u'France': 'fr',
    u'Hrvatska': 'hr',
    u'Italia': 'it',
    u'Magyarország': 'hu',
    u'México': 'mx',
    u'Nederland': 'nl',
    u'Norge': 'no',
    u'Polska': 'pl',
    u'Portugal': 'pt',
    u'Romania': 'ro',
    u'Slovenija': 'si',
    u'Slovensko': 'sk',
    u'Suomi': 'fi',
    u'Sverige': 'se',
    u'Türkiye': 'tr',
    u'United Kingdom': 'en',
    u'USA': 'us',
    u'Ελλάδα': 'gr',
    u'Российская Федерация': 'ru',
    u'台灣': 'tw',
    u'日本': 'jp',
}


class Bogame(QMainWindow):

  def __init__(self):
    super().__init__()
    self.init_ui()

  def init_ui(self):
    self._login = BogameLogin(self)
    self.setCentralWidget(self._login)
    self.setWindowTitle('Bogame')
    self.statusBar().showMessage('Welcome')
    self.center()
    self.show()

  def center(self):
    screen = QDesktopWidget().screenGeometry()
    size = self.geometry()
    self.move((screen.width() - size.width()) / 2,
              (screen.height() - size.height()) / 2)


class ParserWorker(QObject):

  finished = pyqtSignal()

  def __init__(self, login_worker):
    super().__init__()
    self._login_worker = login_worker

  @pyqtSlot()
  def parse(self):
    self._login_worker.get_parser().parse_all()
    self.finished.emit()


class LoginWorker(QObject):

  failed = pyqtSignal(str)
  loggedIn = pyqtSignal(Parser)
  updated = pyqtSignal(int, str)
  finished = pyqtSignal(Parser)

  def __init__(self, country, universe, email, password):
    super().__init__()
    self._country = country
    self._universe = universe
    self._email = email
    self._password = password

  @pyqtSlot()
  def login(self):
    # Login.
    try:
      self._parser = Parser(
          self._country, self._universe, self._email, self._password)
    except ValueError as e:
      self.failed.emit(str(e))
      return
    self.loggedIn.emit(self._parser)

    # Monitor parsing.
    last_status = None
    last_percent = None
    while True:
      status = self._parser.get_parse_stage()
      percent = self._parser.get_parse_percent()
      if (status is not None and percent is not None and
          (status != last_status or percent != last_percent)):
        last_status = status
        last_percent = percent
        self.updated.emit(percent, status)
        if percent == 100:
          self.finished.emit(self._parser)
          break
      time.sleep(1)

  def get_parser(self):
    return self._parser


class BogameLogin(QFrame):

  def __init__(self, parent):
    super().__init__(parent)
    self.init_ui()

  def init_ui(self):
    # Widgets.
    title = QLabel('OGame Login', self)
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet('font: 18pt; margin-bottom: 5px')
    country_label = QLabel('Country', self)
    self._country = QComboBox(self)
    for k in _COUNTRIES.keys():
      self._country.addItem(k)
    universe_label = QLabel('Universe', self)
    self._universe = QLineEdit(self)
    email_label = QLabel('Email address', self)
    self._email = QLineEdit(self)
    password_label = QLabel('Password', self)
    self._password = QLineEdit(self)
    self._password.setEchoMode(QLineEdit.Password)
    login = QPushButton('Login', self)

    # Layout.
    grid = QGridLayout()
    grid.addWidget(title, 0, 0, 1, 2)
    grid.addWidget(country_label, 1, 0)
    grid.addWidget(self._country, 1, 1)
    grid.addWidget(universe_label, 2, 0)
    grid.addWidget(self._universe, 2, 1)
    grid.addWidget(email_label, 3, 0)
    grid.addWidget(self._email, 3, 1)
    grid.addWidget(password_label, 4, 0)
    grid.addWidget(self._password, 4, 1)
    grid.addWidget(login, 5, 0, 1, 2)
    self.setLayout(grid)

    # Behavior.
    self._universe.setValidator(QIntValidator(1, 999, self))
    login.clicked.connect(self.login)

    # Default values from config file.
    config = configparser.ConfigParser()
    config.read('bogame.ini')
    if config.has_section('Login'):
      options = dict(config.items('Login'))
      opt_country = options.get('country')
      if opt_country in _COUNTRIES:
        self._country.setCurrentText(opt_country)
      if self._universe.validator().validate(
          options.get('universe', ''), 0)[0] == QValidator.Acceptable:
        self._universe.setText(options.get('universe', ''))
      self._email.setText(options.get('email', ''))
      self._password.setText(options.get('password' ,''))

  def login(self):
    self.setEnabled(False)
    self.parentWidget().statusBar().showMessage('Logging in...')

    self._login_thread = QThread()
    self._login_worker = LoginWorker(
        _COUNTRIES[self._country.currentText()], self._universe.text(),
        self._email.text(), self._password.text())
    self._login_worker.moveToThread(self._login_thread)

    self._parser_thread = QThread()
    self._parser_worker = ParserWorker(self._login_worker)
    self._parser_worker.moveToThread(self._parser_thread)

    self._login_worker.failed.connect(self.show_login_failure)
    self._login_worker.loggedIn.connect(self._parser_thread.start)
    self._login_worker.updated.connect(self.show_login_progress)
    self._login_worker.finished.connect(self.finish_login)

    qApp.aboutToQuit.connect(self.quit_threads)

    self._login_thread.started.connect(self._login_worker.login)
    self._parser_thread.started.connect(self._parser_worker.parse)

    self._login_thread.start()

  @pyqtSlot(str)
  def show_login_failure(self, error):
    self.setEnabled(True)
    self._login_thread.quit()
    self.parentWidget().statusBar().showMessage('Error: ' + error)

  @pyqtSlot(int, str)
  def show_login_progress(self, percent, status):
    self.parentWidget().statusBar().showMessage(
        'Logging in... {}% - {}'.format(percent, status))

  @pyqtSlot(Parser)
  def finish_login(self, parser):
    self._login_thread.quit()
    self.parentWidget().statusBar().showMessage(
        'Welcome ' + parser.get_player().identity.name)

  @pyqtSlot()
  def quit_threads(self):
    self._login_thread.quit()
    self._parser_thread.quit()


if __name__ == '__main__':
  app = QApplication(sys.argv)
  login = Bogame()
  app.exec_()
  app.deleteLater()
