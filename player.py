import re
import sys

import player_pb2
import scraper


def _parse(x):
  # Strip and remove the dot separator.
  return int(x.strip().replace('.', ''))


def _get_resource(bs, name):
  return _parse(bs.find(id='resources_' + name).string)


def _set_level(bs, id_or_class, message, attr, is_class=False):
  div = bs.find(class_=id_or_class) if is_class else bs.find(id=id_or_class)
  level = int(list(div.find(class_='level').stripped_strings)[1])
  if level > 0:
    message.__setattr__(attr, level)


class Player(object):
  """OGame player."""

  def __init__(self, country, universe, email, password):
    self._scraper = scraper.Scraper(country, universe, email, password)
    self._scraper.login()
    self._player = player_pb2.Player()

  def print_debug(self):
    print self._player

  def scrape_all(self):
    planets = self.scrape_overview()
    self.scrape_scores()
    for i, pair in enumerate(planets):
      planet_id, moon_id = pair
      planet = self._player.planets.add()
      if i == 0:
        planet.is_homeworld = True
      self.scrape_planet(planet_id, planet)
      if moon_id:
        planet.moon.is_moon = True
        planet.moon.coordinates.CopyFrom(planet.coordinates)
        self.scrape_planet(moon_id, planet.moon)

  def scrape_overview(self):
    """Scrape identity and list of planets."""
    bs = self._scraper.get_page('overview')
    self._player.identity.name = bs.find(id='playerName').a.string
    planet_list = bs.find(id='planetList')
    planets = []
    for planet in planet_list.find_all(class_='smallplanet'):
      planet_id = planet['id'].split('-')[1]
      moon = planet.find(class_='moonlink')
      moon_id = moon['href'].split('=')[-1] if moon else None
      planets.append((planet_id, moon_id))
    return planets

  def scrape_scores(self):
    bs = self._scraper.get_page('highscore')
    row = bs.find(class_='myrank')
    self._player.score.points = _parse(row.find(class_='score').string)
    self._player.score.rank = _parse(row.find(class_='position').string)
    self._player.score.honorific_points = _parse(list(
        row.find(class_='honorScore').stripped_strings)[1])
    self._player.score.num_players = int(bs.find(
        class_='changeSite').contents[-2].string.split('-')[1])

  def scrape_planet(self, planet_id, planet):
    planet.id = int(planet_id)
    self.scrape_planet_details(planet_id, planet)
    self.scrape_resources(planet_id, planet)
    self.scrape_mines(planet_id, planet)
    self.scrape_facilities(planet_id, planet)
    self.scrape_research(planet_id, planet)
    self.scrape_shipyard(planet_id, planet)
    self.scrape_defense(planet_id, planet)

  def scrape_planet_details(self, planet_id, planet):
    bs = self._scraper.get_page('overview', planet_id)
    if not planet.is_moon:
      planet.name = bs.find(id='planetNameHeader').string.strip()
      coords = bs.find(
          id='planet-' + planet_id).find(class_='planet-koords').string
      parts = coords[1:-1].split(':')  # e.g. [2:349:10]
      (planet.coordinates.galaxy,
       planet.coordinates.system,
       planet.coordinates.position) = map(int, parts)

  def scrape_resources(self, planet_id, planet):
    bs = self._scraper.get_page('overview', planet_id)
    planet.resources.metal = _get_resource(bs, 'metal')
    planet.resources.crystal = _get_resource(bs, 'crystal')
    planet.resources.deuterium = _get_resource(bs, 'deuterium')
    planet.resources.energy = _get_resource(bs, 'energy')
    planet.resources.dark_matter = _get_resource(bs, 'darkmatter')

  def scrape_mines(self, planet_id, planet):
    bs = self._scraper.get_page('resources', planet_id)
    _set_level(bs, 'button1', planet.mines, 'metal')
    _set_level(bs, 'button2', planet.mines, 'crystal')
    _set_level(bs, 'button3', planet.mines, 'deuterium')
    _set_level(bs, 'button4', planet.mines, 'solar_plant')
    _set_level(bs, 'button5', planet.mines, 'fusion_reactor')
    _set_level(bs, 'button6', planet.mines, 'solar_satellites')
    _set_level(bs, 'button7', planet.mines, 'metal_storage')
    _set_level(bs, 'button8', planet.mines, 'crystal_storage')
    _set_level(bs, 'button9', planet.mines, 'deuterium_storage')

  def scrape_facilities(self, planet_id, planet):
    bs = self._scraper.get_page('station', planet_id)
    _set_level(bs, 'button0', planet.facilities, 'robotics_factory')
    _set_level(bs, 'button1', planet.facilities, 'shipyard')
    if planet.is_moon:
      _set_level(bs, 'button2', planet.facilities, 'lunar_base')
      _set_level(bs, 'button3', planet.facilities, 'sensor_phalanx')
      _set_level(bs, 'button4', planet.facilities, 'jump_gate')
    else:
      _set_level(bs, 'button2', planet.facilities, 'research_lab')
      _set_level(bs, 'button3', planet.facilities, 'alliance_depot')
      _set_level(bs, 'button4', planet.facilities, 'missile_silo')
      _set_level(bs, 'button5', planet.facilities, 'nanite_factory')
      _set_level(bs, 'button6', planet.facilities, 'terraformer')
      _set_level(bs, 'button7', planet.facilities, 'space_dock')

  def scrape_research(self, planet_id, planet):
    bs = self._scraper.get_page('research', planet_id)
    _set_level(bs, 'research113', planet.research, 'energy', is_class=True)
    _set_level(bs, 'research120', planet.research, 'laser', is_class=True)
    _set_level(bs, 'research121', planet.research, 'ion', is_class=True)
    _set_level(bs, 'research114', planet.research, 'hyperspace', is_class=True)
    _set_level(bs, 'research122', planet.research, 'plasma', is_class=True)
    _set_level(bs, 'research106', planet.research, 'espionage', is_class=True)
    _set_level(bs, 'research108', planet.research, 'computer', is_class=True)
    _set_level(bs, 'research124', planet.research, 'astrophysics',
               is_class=True)
    _set_level(bs, 'research123', planet.research, 'intergalactic_network',
               is_class=True)
    _set_level(bs, 'research199', planet.research, 'graviton', is_class=True)
    _set_level(bs, 'research115', planet.research, 'combustion_drive',
               is_class=True)
    _set_level(bs, 'research117', planet.research, 'impulse_drive',
               is_class=True)
    _set_level(bs, 'research118', planet.research, 'hyperspace_drive',
               is_class=True)
    _set_level(bs, 'research109', planet.research, 'weapons', is_class=True)
    _set_level(bs, 'research110', planet.research, 'shielding', is_class=True)
    _set_level(bs, 'research111', planet.research, 'armor', is_class=True)

  def scrape_shipyard(self, planet_id, planet):
    bs = self._scraper.get_page('shipyard', planet_id)
    battleships = bs.find(id='battleships')
    _set_level(battleships, 'button1', planet.shipyard, 'light_fighters')
    _set_level(battleships, 'button2', planet.shipyard, 'heavy_fighers')
    _set_level(battleships, 'button3', planet.shipyard, 'cruisers')
    _set_level(battleships, 'button4', planet.shipyard, 'battleships')
    _set_level(battleships, 'button5', planet.shipyard, 'battlecruisers')
    _set_level(battleships, 'button6', planet.shipyard, 'bombers')
    _set_level(battleships, 'button7', planet.shipyard, 'destroyers')
    _set_level(battleships, 'button8', planet.shipyard, 'deathstars')
    civilships = bs.find(id='civilships')
    _set_level(civilships, 'button1', planet.shipyard, 'small_cargos')
    _set_level(civilships, 'button2', planet.shipyard, 'large_cargos')
    _set_level(civilships, 'button3', planet.shipyard, 'colony_ships')
    _set_level(civilships, 'button4', planet.shipyard, 'recyclers')
    _set_level(civilships, 'button5', planet.shipyard, 'espionage_probes')
    _set_level(civilships, 'button6', planet.shipyard, 'solar_satellites')

  def scrape_defense(self, planet_id, planet):
    bs = self._scraper.get_page('defense', planet_id)
    _set_level(bs, 'defense1', planet.defense, 'rocker_launchers')
    _set_level(bs, 'defense2', planet.defense, 'light_lasers')
    _set_level(bs, 'defense3', planet.defense, 'heavy_lasers')
    _set_level(bs, 'defense4', planet.defense, 'gauss_canons')
    _set_level(bs, 'defense5', planet.defense, 'ion_canons')
    _set_level(bs, 'defense6', planet.defense, 'plasma_turrets')
    _set_level(bs, 'defense7', planet.defense, 'has_small_shield_dome')
    _set_level(bs, 'defense8', planet.defense, 'has_large_shield_dome')
    _set_level(bs, 'defense9', planet.defense, 'anti_ballistic_missiles')
    _set_level(bs, 'defense10', planet.defense, 'interplanetary_missiles')
