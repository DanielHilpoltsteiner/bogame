# -*- coding: utf-8 -*-
import re
import sys

from Tkinter import *
from ttk import *

from parser import Parser

# Change name on OS X.
if sys.platform == 'darwin':
    from Foundation import NSBundle
    bundle = NSBundle.mainBundle()
    if bundle:
        info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
        if info and info['CFBundleName'] == 'Python':
            info['CFBundleName'] = 'Bogame'

_COUNTRIES = {
    'Argentina': 'ar',
    'Brasil': 'br',
    'Danmark': 'dk',
    'Deutschland': 'de',
    'España': 'es',
    'France': 'fr',
    'Hrvatska': 'hr',
    'Italia': 'it',
    'Magyarország': 'hu',
    'México': 'mx',
    'Nederland': 'nl',
    'Norge': 'no',
    'Polska': 'pl',
    'Portugal': 'pt',
    'Romania': 'ro',
    'Slovenija': 'si',
    'Slovensko': 'sk',
    'Suomi': 'fi',
    'Sverige': 'se',
    'Türkiye': 'tr',
    'USA': 'us',
    'United Kingdom': 'en',
    'Česká Republika': 'cz',
    'Ελλάδα': 'gr',
    'Российская Федерация': 'ru',
    '台灣': 'tw',
    '日本': 'jp',
}


class BogameLogin(object):

  def __init__(self):
    self._root = Tk()
    self._root.title('Bogame')
    self._root['menu'] = Menu()
    self._root.resizable(False, False)
    self._frame = Frame(self._root)
    Label(self._frame, text='OGame Login', justify=CENTER,
          font=('Helvetica', 18)).grid(row=0, columnspan=2)
    Label(self._frame, text='Country').grid(row=1, column=0, sticky=E)
    self._country = StringVar()
    Combobox(self._frame, values=sorted(_COUNTRIES.iterkeys()),
             state='readonly', textvariable=self._country,
             background='white').grid(row=1, column=1)
    Label(self._frame, text='Universe').grid(row=2, column=0, sticky=E)
    self._universe = StringVar()
    Entry(self._frame, textvariable=self._universe).grid(row=2, column=1)
    Label(self._frame, text='Email address').grid(row=3, column=0, sticky=E)
    self._email = StringVar()
    Entry(self._frame, textvariable=self._email).grid(row=3, column=1)
    Label(self._frame, text='Password').grid(row=4, column=0, sticky=E)
    self._password = StringVar()
    Entry(self._frame, textvariable=self._password, show='*').grid(row=4,
                                                                   column=1)
    self._login = Button(self._frame, text='Login', command=self.login)
    self._login.grid(row=5, columnspan=2)
    self._error = Label(self._frame, foreground='red')
    self._progress = Progressbar(self._frame, mode='indeterminate')
    self._progress.start()
    for widget in self._frame.winfo_children():
      if widget.grid_info():
        widget.grid_configure(padx=5, pady=2)
    self._frame.pack()
    self._root.bind('<Return>', lambda _: self.login())
    self._i = 0

  def run(self):
    self._root.mainloop()

  def validate_inputs(self, country, universe, email, password):
    if not country:
      return 'No country selected'
    if not universe:
      return 'No universe entered'
    if not email:
      return 'No email address entered'
    if not password:
      return 'No password entered'
    try:
      universe = int(universe)
    except ValueError:
      return 'Universe should be in 1...199'
    if not 0 < universe < 200:
      return 'Universe should be in 1...199'
    if not re.match(
        r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$',
        email):
      return 'Invalid email address'

  def print_error(self, error):
    self._progress.grid_remove()
    self._error['text'] = error
    self._error.grid(row=5, columnspan=2, padx=5, pady=2)
    self._login.grid(row=6, columnspan=2, padx=5, pady=2)

  def login(self):
    self._error.grid_remove()
    self._login.grid_remove()
    self._progress.grid(row=5, columnspan=2, padx=5, pady=2)
    (country, universe, email, password) = (
        self._country.get(), self._universe.get(), self._email.get(),
        self._password.get())
    error = self.validate_inputs(country, universe, email, password)
    if error:
      self.print_error(error)
      return
    try:
      parser = Parser(_COUNTRIES[country], universe, email, password)
    except ValueError as e:
      self.print_error(str(e))
      return
    self.print_error('SUCCESS')


if __name__ == '__main__':
  BogameLogin().run()
