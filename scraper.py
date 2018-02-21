import logging

import bs4
import mechanize


class Scraper(object):
  """Scraper for OGame."""

  def __init__(self, country, universe, email, password):
    self._country = country
    self._universe = universe
    self._email = email
    self._password = password
    self._login_url = 'https://{}.ogame.gameforge.com/'.format(country)
    self._url = 'https://s{}-{}.ogame.gameforge.com/game/index.php'.format(
        universe, country)
    self._browser = mechanize.Browser()
    self._browser.set_handle_robots(False)
    self._browser.set_header(
        'user-agent',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36')
    self._cached_pages = {}
    self._logger = logging.getLogger('bogame')

  def login(self):
    """Login with given credentials."""
    self._browser.open(self._login_url)
    self._browser.select_form(name='loginForm')
    form = self._browser.form
    form['login'] = self._email
    form['pass'] = self._password
    form['uni'] = ['s{}-{}.ogame.gameforge.com'.format(
        self._universe, self._country)]
    self._browser.submit()
    if 's{}-{}.'.format(
        self._universe, self._country) not in self._browser.geturl():
      raise ValueError('Invalid credentials')

  def get_page(self, page, planet=None):
    """Get parsed requested page."""
    if (page, planet) not in self._cached_pages:
      url = self._url + '?page=' + page
      if planet:
        url += '&cp=' + planet
      self._logger.info('Fetching ' + url)
      response = self._browser.open(url)
      self._cached_pages[page, planet] = bs4.BeautifulSoup(
          response.read(), 'lxml')
    return self._cached_pages[page, planet]

  def clear_cache(self):
    self._cached_pages = {}
