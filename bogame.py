# -*- coding: utf-8 -*-

### DEPRECATED ###

import argparse
import configparser
import sys
import threading
import time

from tkinter import *
from tkinter.ttk import *

from parser import Parser
import player_pb2
import report_lib

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

  def __init__(self, root, player):
    Frame.__init__(self, root)
    self._root = root
    self._player = player

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
    Combobox(self._form, values=sorted(_COUNTRIES.keys()),
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
    self._progress_bar = Progressbar(self._progress, mode='indeterminate',
                                     length=250)
    self._progress_bar.start()
    self._progress_bar.pack()

    # Key binding.
    root.bind('<Return>', lambda _: self.login())

    # Default values from config file.
    config = configparser.ConfigParser()
    config.read('bogame.ini')
    if config.has_section('Login'):
      options = dict(config.items('Login'))
      country = options.get('country')
      if country in _COUNTRIES:
        self._country.set(country)
      self._universe.set(options.get('universe', ''))
      self._email.set(options.get('email', ''))
      self._password.set(options.get('password' ,''))

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
        percent = self._parser.get_parse_percent()
        if percent is not None:
          self._progress_bar['mode'] = 'determinate'
          self._progress_bar.stop()
          self._progress_bar['value'] = percent
        if self._parser.get_parse_stage() == 'Completed':
          self._exit()
          return

  def _exit(self):
    self._player.CopyFrom(self._parser._player)
    self._root.quit()


class BogameMain(Frame):

  def __init__(self, root, player):
    Frame.__init__(self, root)
    y_scroll = Scrollbar(self, orient=VERTICAL)
    y_scroll.grid(row=0, column=1, sticky=NS)
    x_scroll = Scrollbar(self, orient=HORIZONTAL)
    x_scroll.grid(row=1, column=0, sticky=EW)
    tabs = Notebook(self)
    tabs.grid(row=0, column=0, sticky=NSEW)

    # --- Energy report ---
    energy_report = Notebook(tabs)
    for planet in player.planets:
      report = Listbox(energy_report, xscrollcommand=x_scroll.set,
                       yscrollcommand=y_scroll.set)
      x_scroll['command'] = report.xview
      y_scroll['command'] = report.yview
      for line in str(report_lib.generate_energy_report(player,
                                                        planet)).split('\n'):
        report.insert(END, line)
      energy_report.add(report, text=planet.name)
    tabs.add(energy_report, text="Energy")

    # --- Full details ---
    player_details = Listbox(tabs, xscrollcommand=x_scroll.set,
                           yscrollcommand=y_scroll.set)
    # TODO: Stickiness doesn't really work on resize.
    x_scroll['command'] = player_details.xview
    y_scroll['command'] = player_details.yview
    for line in str(player).split('\n'):
      player_details.insert(END, line)
    tabs.add(player_details, text="Details")


if __name__ == '__main__':
  # Skip login/scraping and use saved file.
  arg_parser = argparse.ArgumentParser()
  arg_parser.add_argument('-i', '--input', type=str, help='Output of parse.py')
  args = arg_parser.parse_args()

  root, login = None, None
  player = player_pb2.Player()
  if args.input:
    with open(args.input, 'rb') as f:
      player.ParseFromString(f.read())
  else:
    # Login.
    root = Tk()
    root.title('Bogame')
    root.resizable(False, False)
    root['menu'] = Menu()
    login = BogameLogin(root, player).pack()
    root.mainloop()
    # TODO: Stop running threads, if any.

  # Main.
  if player.ByteSize():
    root = Tk()
    # TODO: Clear the BogameLogin frame, if any.
    root.title('Bogame')
    root.resizable(True, True)
    root['menu'] = Menu()
    BogameMain(root, player).pack(fill=BOTH)
    root.mainloop()
