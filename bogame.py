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
    u'Argentina': 'ar',
    u'Brasil': 'br',
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
    u'USA': 'us',
    u'United Kingdom': 'en',
    u'Česká Republika': 'cz',
    u'Ελλάδα': 'gr',
    u'Российская Федерация': 'ru',
    u'台灣': 'tw',
    u'日本': 'jp',
}


class BogameLogin(Frame):

  def __init__(self, root):
    Frame.__init__(self, root)
    Label(self, text='OGame Login', justify=CENTER,
          font=('Helvetica', 18)).grid(row=0, columnspan=2)
    Label(self, text='Country').grid(row=1, column=0, sticky=E)
    self._country = StringVar()
    Combobox(self, values=sorted(_COUNTRIES.iterkeys()),
             state='readonly', textvariable=self._country,
             background='white').grid(row=1, column=1)
    Label(self, text='Universe').grid(row=2, column=0, sticky=E)
    self._universe = StringVar()
    Entry(self, textvariable=self._universe).grid(row=2, column=1)
    Label(self, text='Email address').grid(row=3, column=0, sticky=E)
    self._email = StringVar()
    Entry(self, textvariable=self._email).grid(row=3, column=1)
    Label(self, text='Password').grid(row=4, column=0, sticky=E)
    self._password = StringVar()
    Entry(self, textvariable=self._password, show='*').grid(row=4,
                                                                   column=1)
    self._login = Button(self, text='Login', command=self.login)
    self._login.grid(row=5, columnspan=2)
    self._error = Label(self, foreground='red')
    self._progress = Progressbar(self, mode='indeterminate')
    self._progress.start()
    for widget in self.winfo_children():
      if widget.grid_info():
        widget.grid_configure(padx=5, pady=2)
    self.pack()
    root.bind('<Return>', lambda _: self.login())
    self._i = 0

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
  root = Tk()
  root.title('Bogame')
  root.resizable(False, False)
  root['menu'] = Menu()
  BogameLogin(root)
  root.mainloop()
