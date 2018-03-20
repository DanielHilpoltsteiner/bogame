import math

from bogame.analysis import energy_pb2
from bogame.core import player_pb2
from bogame.core.formulae import *


def generate_energy_report(player, planet):
  energy = energy_pb2.EnergyReport()
  p = py_expression_eval.Parser()

  # Influencing parameters.
  energy.has_engineer = player.officers.has_engineer
  energy.mean_temperature = (
      planet.max_temperature + planet.min_temperature) / 2
  energy.energy_technology = player.research.energy
  energy.universe_speed = player.universe.speed

  # Energy needed for mines.
  energy.metal_level = planet.mines.metal
  energy.crystal_level = planet.mines.crystal
  energy.deuterium_level = planet.mines.deuterium
  metal_level = float(planet.mines.metal)
  crystal_level = float(planet.mines.crystal)
  deuterium_level = float(planet.mines.deuterium)
  energy.metal_production_rate = planet.production_rates.metal
  energy.crystal_production_rate = planet.production_rates.crystal
  energy.deuterium_production_rate = planet.production_rates.deuterium
  energy.metal_energy_consumption = F(MET_ENERGY_CONSUMPTION, L=metal_level)
  energy.crystal_energy_consumption = F(CRY_ENERGY_CONSUMPTION, L=crystal_level)
  energy.deuterium_energy_consumption = F(DEU_ENERGY_CONSUMPTION,
                                          L=deuterium_level)
  energy.total_energy_consumption = (energy.metal_energy_consumption +
      energy.crystal_energy_consumption + energy.deuterium_energy_consumption)

  # Solar plant.
  energy.solar_plant_level = planet.mines.solar_plant
  solar_level = float(energy.solar_plant_level)
  energy.solar_plant_production_rate = planet.production_rates.solar_plant
  energy.solar_plant_nominal_output = F(SOLAR_PLANT_OUTPUT, L=solar_level)
  engineer_boost = 1.1 if energy.has_engineer else 1.0
  energy.solar_plant_actual_output = int(
      energy.solar_plant_nominal_output * energy.solar_plant_production_rate *
      engineer_boost)
  energy.solar_plant_fraction_of_energy_needed = (
      float(energy.solar_plant_actual_output) / energy.total_energy_consumption
      if energy.total_energy_consumption else float('nan'))

  # Fusion reactor.
  energy.fusion_reactor_level = planet.mines.fusion_reactor
  fusion_level = float(energy.fusion_reactor_level)
  energy.fusion_reactor_production_rate = planet.production_rates.fusion_reactor
  energy_technology = float(player.research.energy)
  energy.fusion_reactor_nominal_output = F(FUSION_REACTOR_OUTPUT,
                                           L=fusion_level, ET=energy_technology)
  energy.fusion_reactor_actual_output = int(
      energy.fusion_reactor_nominal_output *
      energy.fusion_reactor_production_rate * engineer_boost)
  energy.fusion_reactor_nominal_deuterium_consumption = F(
      FUSION_REACTOR_DEU_CONSUMPTION, L=fusion_level, US=energy.universe_speed)
  energy.fusion_reactor_actual_deuterium_consumption = int(
      energy.fusion_reactor_nominal_deuterium_consumption *
      energy.fusion_reactor_production_rate)
  energy.fusion_reactor_fraction_of_energy_needed = (
      float(energy.fusion_reactor_actual_output) /
            energy.total_energy_consumption
      if energy.total_energy_consumption else float('nan'))

  # Solar satellites.
  energy.solar_satellite_singular_nominal_output = F(SOLAR_SATELLITE_OUTPUT,
                                                     T=energy.mean_temperature)
  energy.solar_satellite_number = planet.shipyard.solar_satellites
  energy.solar_satellite_production_rate = (
      planet.production_rates.solar_satellites)
  energy.solar_satellite_nominal_output = int(energy.solar_satellite_number *
      energy.solar_satellite_singular_nominal_output)
  energy.solar_satellite_actual_output = int(
      energy.solar_satellite_nominal_output *
      energy.solar_satellite_production_rate * engineer_boost)
  energy.solar_satellite_fraction_of_energy_needed = (
      float(energy.solar_satellite_actual_output) /
            energy.total_energy_consumption
      if energy.total_energy_consumption else float('nan'))
  energy.satellites_needed_to_replace_fusion_reactor = int(math.ceil(
      float(energy.fusion_reactor_actual_output) /
      energy.solar_satellite_singular_nominal_output))

  # Total energy.
  energy.nominal_output = (energy.solar_plant_nominal_output +
                           energy.fusion_reactor_nominal_output +
                           energy.solar_satellite_nominal_output)
  energy.actual_output = (energy.solar_plant_actual_output +
                          energy.fusion_reactor_actual_output +
                          energy.solar_satellite_actual_output)
  energy.needed_energy = energy.total_energy_consumption
  energy.available_energy = energy.actual_output - energy.needed_energy

  return energy
