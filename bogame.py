# -*- coding: utf-8 -*-
import sys
import threading
import time

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

    # Form vars.
    self._country = StringVar()
    self._universe = StringVar()
    self._email = StringVar()
    self._password = StringVar()

    # Form.
    self._form = Frame(self)
    Label(self._form, text='OGame Login', justify=CENTER,
          font=('Helvetica', 16)).grid(columnspan=2)
    for row, label in enumerate([
        'Country', 'Universe', 'Email address', 'Password'], start=1):
        Label(self._form, text=label).grid(row=row, column=0, sticky=E)
    Combobox(self._form, values=sorted(_COUNTRIES.iterkeys()),
             state='readonly', textvariable=self._country,
             background='white').grid(row=1, column=1)
    Entry(self._form, textvariable=self._universe).grid(row=2, column=1)
    Entry(self._form, textvariable=self._email).grid(row=3, column=1)
    Entry(self._form, textvariable=self._password, show='*').grid(row=4,
                                                                  column=1)
    self._login = Button(self._form, text='Login', command=self.login)
    self._login.grid(row=5, columnspan=2)
    self._error = Label(self._form, foreground='red')
    for widget in self._form.winfo_children():
      if widget.grid_info():
        widget.grid_configure(padx=5, pady=2)
    self._form.pack()

    # Progress bar.
    self._progress = Frame(self)
    self._progress_text = Label(self._progress, text='Logging in...')
    self._progress_text.pack()
    progress_bar = Progressbar(self._progress, mode='indeterminate', length=250)
    progress_bar.start()
    progress_bar.pack()

    # Key binding.
    root.bind('<Return>', lambda _: self.login())

  def print_error(self, error):
    self._progress.pack_forget()
    self._error['text'] = error
    self._error.grid(row=5, columnspan=2, padx=5, pady=2)
    self._login.grid(row=6, columnspan=2, padx=5, pady=2)
    self._form.pack()

  def login(self):
    self._form.pack_forget()
    self._progress.pack()
    (country, universe, email, password) = (
        self._country.get(), self._universe.get(), self._email.get(),
        self._password.get())
    if country not in _COUNTRIES:
      self.print_error('No country selected')
      return
    self._parser = None
    threading.Thread(
        target=self.do_login,
        args=(_COUNTRIES[country], universe, email, password)).start()
    threading.Thread(
        target=self.show_progress,
        args=()).start()

  def do_login(self, country, universe, email, password):
    try:
      self._parser = Parser(country, universe, email, password)
    except ValueError as e:
      self.print_error(str(e))
      return
    self._parser.parse_all()

  def show_progress(self):
    while True:
      time.sleep(1)
      if self._parser:
        self._progress_text['text'] = self._parser.get_parse_stage()
        if self._parser.get_parse_stage() == 'Completed':
          print self._parser._player
          return

if __name__ == '__main__':
  root = Tk()
  root.title('Bogame')
  root.resizable(False, False)
  root['menu'] = Menu()
  BogameLogin(root).pack()
  root.mainloop()
