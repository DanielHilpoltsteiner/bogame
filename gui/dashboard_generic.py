from PyQt5.QtCore import (
    Qt,
)
from PyQt5.QtWidgets import (
    QFrame,
    QTableWidget,
    QVBoxLayout,
)
from bogame.gui.widgets import (
    TableHeaderLine,
    TableItem,
)


class GenericDashboard(QFrame):

  def __init__(self, player, protos, parent):
    super().__init__(parent)
    self._player = player
    self._protos = protos
    self.init_ui()

  def labels(self):
    """List of row labels. Use ***X*** to group rows."""
    raise NotImplementedError

  def fill_entries(self, proto, add, add_shared, skip):
    """Call functions add/skip for each entry in the proto."""
    raise NotImplementedError

  def init_ui(self):
    num_planets = len(self._protos)

    # Headers.
    labels = self.labels()
    table = QTableWidget(self)
    table.setColumnCount(num_planets)
    table.setRowCount(len(labels))
    table.setHorizontalHeaderLabels([
        (u'🌓   ' if x[0].is_moon else u'🌎   ') + x[0].name
        for x in self._protos])
    table.setVerticalHeaderLabels([
        x if not x.startswith('*') else '' for x in labels])
    for r, label in enumerate(labels):
      if label.startswith('*'):
        table.setItem(r, 0, TableHeaderLine(label.strip('*')))
        table.setSpan(r, 0, 1, num_planets)

    # Entries.
    for i, proto in enumerate(x[1] for x in self._protos):
      r = 0

      def add(text):
        nonlocal r
        string = '{:n}'.format(text) if isinstance(text, int) else str(text)
        table.setItem(r, i, TableItem(string))
        r += 1

      def add_shared(text):
        nonlocal r
        if i == 0:
          string = '{:n}'.format(text) if isinstance(text, int) else str(text)
          item = TableItem(string)
          item.setTextAlignment(Qt.AlignCenter)
          table.setItem(r, i, item)
          table.setSpan(r, i, 1, num_planets)
        r += 1

      def skip():
        nonlocal r
        r += 1

      self.fill_entries(proto, add, add_shared, skip)
    table.resizeColumnsToContents()

    grid = QVBoxLayout(self)
    grid.addWidget(table)
    self.setLayout(grid)
