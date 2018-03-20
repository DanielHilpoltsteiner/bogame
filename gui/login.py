"""Login GUI."""
import configparser
import time

from PyQt5.QtCore import (
    pyqtSignal,
    pyqtSlot,
    QObject,
    Qt,
    QThread,
)
from PyQt5.QtGui import (
    QIntValidator,
    QValidator,
)
from PyQt5.QtWidgets import (
    qApp,
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

from bogame.core.player_pb2 import Player
from bogame.scraper.scraper import Scraper

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


class LoginWindow(QMainWindow):

  finished = pyqtSignal(Player)

  def __init__(self):
    super().__init__()
    self.init_ui()

  def init_ui(self):
    self._login = Login(self)
    self._login.finished.connect(self.finish)
    self.setCentralWidget(self._login)
    self.setWindowTitle('Bogame')
    self.statusBar().showMessage('Welcome')
    self.center()
    self.show()

  def center(self):
    resolution = QDesktopWidget().screenGeometry()
    self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
              (resolution.height() / 2) - (self.frameSize().height() / 2))

  @pyqtSlot(Scraper)
  def finish(self, scraper):
    self.finished.emit(scraper.get_player())
    self.hide()


class Login(QFrame):

  finished = pyqtSignal(Scraper)

  def __init__(self, parent):
    super().__init__(parent)
    self.init_ui()
    self._login_thread = None
    self._scraper_thread = None
    self._threads = []  # prevent garbage collection

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
    self.parentWidget().statusBar().showMessage('Logging in...')

    # Progress dialog.
    self._progress = QProgressDialog('Logging in...', 'Cancel', 0, 100, self)
    self._progress.setAutoClose(True)
    self._progress.setModal(True)
    self._progress.setMinimumDuration(0)
    self._progress.setMinimumWidth(300)
    self._progress.setVisible(True)

    if self._login_thread is not None:
      self._threads.append(self._login_thread)
    self._login_thread = QThread()
    self._login_worker = LoginWorker(
        _COUNTRIES[self._country.currentText()], self._universe.text(),
        self._email.text(), self._password.text())
    self._login_worker.moveToThread(self._login_thread)

    if self._scraper_thread is not None:
      self._threads.append(self._scraper_thread)
    self._scraper_thread = QThread()
    self._scraper_worker = ScraperWorker(self._login_worker)
    self._scraper_worker.moveToThread(self._scraper_thread)

    self._login_worker.failed.connect(self.show_login_failure)
    self._login_worker.loggedIn.connect(self._scraper_thread.start)
    self._login_worker.updated.connect(self.show_login_progress)
    self._login_worker.finished.connect(self.finish_login)

    self._progress.canceled.connect(self.quit_threads)
    qApp.aboutToQuit.connect(self.quit_threads)

    self._login_thread.started.connect(self._login_worker.login)
    self._scraper_thread.started.connect(self._scraper_worker.parse)

    self._login_thread.start()

  @pyqtSlot(str)
  def show_login_failure(self, error):
    self._login_thread.quit()
    self.parentWidget().statusBar().showMessage('Error: ' + error)
    self._progress.setVisible(False)

  @pyqtSlot(int, str)
  def show_login_progress(self, percent, status):
    self._progress.setLabelText(status)
    self._progress.setValue(percent)

  @pyqtSlot(Scraper)
  def finish_login(self, scraper):
    self._login_thread.quit()
    self.parentWidget().statusBar().showMessage(
        'Welcome, {}!'.format(scraper.get_player().identity.name))
    self.finished.emit(scraper)

  @pyqtSlot()
  def quit_threads(self):
    self.parentWidget().statusBar().showMessage('Welcome')
    self._login_thread.quit()
    self._scraper_thread.quit()
    self._login_worker.cancel()
    self._scraper_worker.cancel_if_not_finished()


class LoginWorker(QObject):

  failed = pyqtSignal(str)
  loggedIn = pyqtSignal(Scraper)
  updated = pyqtSignal(int, str)
  finished = pyqtSignal(Scraper)

  def __init__(self, country, universe, email, password):
    super().__init__()
    self._country = country
    self._universe = universe
    self._email = email
    self._password = password
    self._is_canceled = False

  def cancel(self):
    self._is_canceled = True

  @pyqtSlot()
  def login(self):
    # Login.
    try:
      self._scraper = Scraper(
          self._country, self._universe, self._email, self._password)
    except ValueError as e:
      self.failed.emit(str(e))
      return
    if self._is_canceled:
      return
    self.loggedIn.emit(self._scraper)

    # Monitor parsing.
    last_status = None
    last_percent = None
    while True:
      status = self._scraper.get_parse_stage()
      percent = self._scraper.get_parse_percent()
      if (status is not None and percent is not None and
          (status != last_status or percent != last_percent)):
        last_status = status
        last_percent = percent
        self.updated.emit(percent, status)
        if status == 'Completed':
          self.finished.emit(self._scraper)
          break
      time.sleep(1)

  def get_scraper(self):
    return self._scraper


class ScraperWorker(QObject):

  def __init__(self, login_worker):
    super().__init__()
    self._login_worker = login_worker
    self._started = False
    self._finished = False

  @pyqtSlot()
  def parse(self):
    self._started = True
    self._login_worker.get_scraper().parse_all()
    self._finished = True

  def cancel_if_not_finished(self):
    if self._started and not self._finished:
      self._login_worker.get_scraper().cancel()
