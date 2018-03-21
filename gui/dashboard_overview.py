from PyQt5.QtCore import (
    Qt,
    QDateTime,
)

from bogame.gui import dashboard_generic


class OverviewDashboard(dashboard_generic.GenericDashboard):

  def labels(self):
    return [
        '***Overview***',
        'Last scraped',
        'Player name',
        'Alliance',
        'Points',
        'Honorific points',
        'Rank',
        '***Planet***',
        'Name',
        'Coordinates',
        'Diameter',
        'Size/capacity',
        'Temperature',
        '***Resources***',
        'Metal',
        'Crystal',
        'Deuterium',
        'Energy',
        'Dark matter',
        '***Production***',
        'Metal',
        'Crystal',
        'Deuterium',
        'Solar plant',
        'Fusion reactor',
        'Solar satellites',
        'Metal storage',
        'Crystal storage',
        'Deuterium storage',
        '***Facilities***',
        'Robotics factory',
        'Shipyard',
        'Research lab',
        'Missile silo',
        'Nanite factory',
        'Space dock',
        'Lunar base',
        'Sensor phalanx',
        'Jump gate',
        '***Research***',
        'Energy',
        'Laser',
        'Ion',
        'Hyperspace',
        'Plasma',
        'Espionage',
        'Computer',
        'Astrophysics',
        'Combustion drive',
        'Impulse drive',
        'Hyperspace drive',
        'Weapons',
        'Shielding',
        'Armor',
        '***Fleet***',
        'Light fighters',
        'Heavy fighters',
        'Cruisers',
        'Battleships',
        'Battlecruisers',
        'Bombers',
        'Destroyers',
        'Deathstars',
        'Small cargos',
        'Large cargos',
        'Colony ships',
        'Recyclers',
        'Espionage probes',
        'Solar satellites',
        '***Defense***',
        'Rocket launchers',
        'Light lasers',
        'Heavy lasers',
        'Gauss canons',
        'Ion canons',
        'Plasma turrets',
        'Anti ballistic missiles',
        'Interplanetary missiles',
        'Small shield dome',
        'Large shield dome',
        '***Universe***',
        'Name',
        'Speed',
        'Fleet speed',
        'Donut galaxy',
        'Donut system',
        '***Officers***',
        'Commander',
        'Admiral',
        'Engineer',
        'Geologist',
        'Technocrat',
    ]

  def fill_entries(self, planet, add, add_shared, skip):
    skip()
    add_shared(QDateTime.fromMSecsSinceEpoch(
        self._player.timestamp * 1000,
        Qt.LocalTime).toString(
            Qt.DefaultLocaleLongDate))
    add_shared(self._player.identity.name)
    if self._player.identity.HasField('alliance_name'):
      add_shared('{} ({})'.format(self._player.identity.alliance_name,
                                  self._player.identity.alliance_tag))
    else:
      add_shared('')
    add_shared(self._player.score.points)
    add_shared(self._player.score.honorific_points)
    add_shared('{} / {}'.format(self._player.score.rank,
                                self._player.score.num_players))

    skip()
    add(planet.name)
    add('{}:{}:{}'.format(planet.coordinates.galaxy,
                          planet.coordinates.system,
                          planet.coordinates.position))
    add('{} km'.format(planet.diameter_km))
    add('{} / {}'.format(planet.size, planet.capacity))
    add('{} ºC to {} ºC'.format(planet.min_temperature, planet.max_temperature))

    skip()
    add(planet.resources.metal)
    add(planet.resources.crystal)
    add(planet.resources.deuterium)
    add(planet.resources.energy)
    add_shared(planet.resources.dark_matter)

    skip()
    if planet.mines.metal:
      add('Lvl {} ({}x)'.format(planet.mines.metal,
                                planet.production_rates.metal))
    else: skip()
    if planet.mines.crystal:
      add('Lvl {} ({}x)'.format(planet.mines.crystal,
                                planet.production_rates.crystal))
    else: skip()
    if planet.mines.deuterium:
      add('Lvl {} ({}x)'.format(planet.mines.deuterium,
                                planet.production_rates.deuterium))
    else: skip()
    if planet.mines.solar_plant:
      add('Lvl {} ({}x)'.format(planet.mines.solar_plant,
                                planet.production_rates.solar_plant))
    else: skip()
    if planet.mines.fusion_reactor:
       add('Lvl {} ({}x)'.format(planet.mines.fusion_reactor,
                                planet.production_rates.fusion_reactor))
    else: skip()
    if planet.shipyard.solar_satellites:
      add('{} ({}x)'.format(planet.shipyard.solar_satellites,
                                planet.production_rates.solar_satellites))
    else: skip()
    add('Lvl {}'.format(planet.mines.metal_storage))
    add('Lvl {}'.format(planet.mines.crystal_storage))
    add('Lvl {}'.format(planet.mines.deuterium_storage))

    skip()
    for facility in [
        'robotics_factory',
        'shipyard',
        'research_lab',
        'missile_silo',
        'nanite_factory',
        'space_dock',
        'lunar_base',
        'sensor_phalanx',
        'jump_gate',
    ]:
      level = getattr(planet.facilities, facility)
      if level:
        add('Lvl {}'.format(level))
      else:
        skip()

    skip()
    for research in [
        'energy',
        'laser',
        'ion',
        'hyperspace',
        'plasma',
        'espionage',
        'computer',
        'astrophysics',
        'combustion_drive',
        'impulse_drive',
        'hyperspace_drive',
        'weapons',
        'shielding',
        'armor',
    ]:
      level = getattr(self._player.research, research)
      if level:
        add_shared('Lvl {}'.format(level))
      else:
        skip()

    skip()
    for vessel in [
        'light_fighters',
        'heavy_fighters',
        'cruisers',
        'battleships',
        'battlecruisers',
        'bombers',
        'destroyers',
        'deathstars',
        'small_cargos',
        'large_cargos',
        'colony_ships',
        'recyclers',
        'espionage_probes',
        'solar_satellites',
    ]:
      num = getattr(planet.shipyard, vessel)
      if num:
        add(num)
      else:
        skip()

    skip()
    for defense in [
        'rocket_launchers',
        'light_lasers',
        'heavy_lasers',
        'gauss_canons',
        'ion_canons',
        'plasma_turrets',
        'anti_ballistic_missiles',
        'interplanetary_missiles',
    ]:
      num = getattr(planet.defense, defense)
      if num:
        add(num)
      else:
        skip()
    add('Yes' if planet.defense.has_small_shield_dome else 'No')
    add('Yes' if planet.defense.has_large_shield_dome else 'No')

    skip()
    add_shared(self._player.universe.name)
    add_shared(self._player.universe.speed)
    add_shared(self._player.universe.fleet_speed)
    add_shared('Yes' if self._player.universe.donut_galaxy else 'No')
    add_shared('Yes' if self._player.universe.donut_system else 'No')

    skip()
    add_shared('Yes' if self._player.officers.has_commander else 'No')
    add_shared('Yes' if self._player.officers.has_admiral else 'No')
    add_shared('Yes' if self._player.officers.has_engineer else 'No')
    add_shared('Yes' if self._player.officers.has_geologist else 'No')
    add_shared('Yes' if self._player.officers.has_technocrat else 'No')
