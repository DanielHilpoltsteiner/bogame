from PyQt5.QtCore import (
    Qt,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QFont,
)
from PyQt5.QtWidgets import (
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
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


class EnergyDashboard(QFrame):

  def __init__(self, reports, parent):
    super().__init__(parent)
    self._reports = reports
    self.init_ui()

  def init_ui(self):
    num_planets = len(self._reports)
    labels = [
        '***Overview***',
        'Nominal output',
        'Actual output',
        'Energy needed',
        'Energy available',
        'Energy utilization',
        '***Solar Plant***',
        'Level',
        'Production rate',
        'Nominal output',
        'Actual output',
        'Fraction of energy needed',
        '***Fusion Reactor***',
        'Level',
        'Production rate',
        'Nominal output',
        'Actual output',
        'Nominal deuterium consumption',
        'Actual deuterium consumption',
        'Fraction of energy needed',
        'Satellites needed to replace',
        '***Solar Satellites***',
        'Singular nominal output',
        'Number',
        'Production rate',
        'Nominal output',
        'Actual output',
        'Fraction of energy needed',
        '***Energy Consumption***',
        'Metal level',
        'Crystal level',
        'Deuterium level',
        'Metal production rate',
        'Crystal production rate',
        'Deuterium production rate',
        'Metal energy consumption',
        'Crystal energy consumption',
        'Deuterium energy consumption',
        'Total energy consumption',
        '***Influencing Parameters***',
        'Engineer',
        'Mean temperature',
        'Energy technology',
        'Universe speed',
    ]

    # Headers.
    table = QTableWidget(self)
    table.setColumnCount(num_planets)
    table.setRowCount(len(labels))
    table.setHorizontalHeaderLabels([
        (u'🌓   ' if x[0].is_moon else u'🌎   ') + x[0].name
        for x in self._reports])
    table.setVerticalHeaderLabels([
        x if not x.startswith('*') else '' for x in labels])
    for r, label in enumerate(labels):
      if label.startswith('*'):
        table.setItem(r, 0, TableHeaderLine(label.strip('*')))
        table.setSpan(r, 0, 1, num_planets)

    # Entries.
    for i, report in enumerate(x[1] for x in self._reports):
      r = 0

      def add(text):
        nonlocal r
        table.setItem(r, i, TableItem(str(text)))
        r += 1

      def add_shared(text):
        nonlocal r
        if i == 0:
          item = TableItem(str(text))
          item.setTextAlignment(Qt.AlignCenter)
          table.setItem(r, i, item)
          table.setSpan(r, i, 1, num_planets)
        r += 1

      def skip():
        nonlocal r
        r += 1

      skip()
      add(report.nominal_output)
      add(report.actual_output)
      add(report.needed_energy)
      add(report.available_energy)
      add('{:.2%}'.format(report.energy_utilization))
      skip()
      add(report.solar_plant_level)
      add(report.solar_plant_production_rate)
      add(report.solar_plant_nominal_output)
      add(report.solar_plant_actual_output)
      add('{:.2%}'.format(report.solar_plant_fraction_of_energy_needed))
      skip()
      add(report.fusion_reactor_level)
      add(report.fusion_reactor_production_rate)
      add(report.fusion_reactor_nominal_output)
      add(report.fusion_reactor_actual_output)
      add(report.fusion_reactor_nominal_deuterium_consumption)
      add(report.fusion_reactor_actual_deuterium_consumption)
      add('{:.2%}'.format(report.fusion_reactor_fraction_of_energy_needed))
      add(report.satellites_needed_to_replace_fusion_reactor)
      skip()
      add(report.solar_satellite_singular_nominal_output)
      add(report.solar_satellite_number)
      add(report.solar_satellite_production_rate)
      add(report.solar_satellite_nominal_output)
      add(report.solar_satellite_actual_output)
      add('{:.2%}'.format(report.solar_satellite_fraction_of_energy_needed))
      skip()
      add(report.metal_level)
      add(report.crystal_level)
      add(report.deuterium_level)
      add(report.metal_production_rate)
      add(report.crystal_production_rate)
      add(report.deuterium_production_rate)
      add(report.metal_energy_consumption)
      add(report.crystal_energy_consumption)
      add(report.deuterium_energy_consumption)
      add(report.total_energy_consumption)
      skip()
      add_shared('Yes' if report.has_engineer else 'No')
      add(report.mean_temperature)
      add_shared(report.energy_technology)
      add_shared(report.universe_speed)
    table.resizeColumnsToContents()

    grid = QVBoxLayout(self)
    grid.addWidget(table)
    self.setLayout(grid)
