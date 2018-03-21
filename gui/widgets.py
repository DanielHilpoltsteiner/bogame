from PyQt5.QtCore import (
    Qt,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QFont,
)
from PyQt5.QtWidgets import (
    QTableWidgetItem,
)

class TableHeaderLine(QTableWidgetItem):

  def __init__(self, string):
    super().__init__(string)
    self.setFlags(Qt.ItemIsEnabled)
    self.setTextAlignment(Qt.AlignCenter)
    self.setBackground(QBrush(QColor(97, 154, 244)))
    font = QFont()
    font.setBold(True)
    font.setCapitalization(QFont.SmallCaps)
    self.setFont(font)


class TableItem(QTableWidgetItem):

  def __init__(self, string):
    super().__init__(string)
    self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
