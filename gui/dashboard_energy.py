from bogame.gui import dashboard_generic


class EnergyDashboard(dashboard_generic.GenericDashboard):

  def labels(self):
    return [
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

  def fill_entries(self, report, add, add_shared, skip):
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
