import re
import sys
import time

import bs4

import player_pb2
import scraper


def _parse(x):
  # Strip and remove the dot separator.
  return int(x.strip().replace('.', ''))


def _get_resource(bs, name):
  return _parse(bs.find(id='resources_' + name).string)


def _set_level(bs, id_or_class, message, attr, is_class=False):
  div = bs.find(class_=id_or_class) if is_class else bs.find(id=id_or_class)
  level = int(list(div.find(class_='level').stripped_strings)[-1])
  if level > 0:
    message.__setattr__(attr, level)


def _get_meta(bs, name):
  metas = bs.find_all('meta')
  return [m for m in metas if m.get('name') == name][0]['content']


class Parser(object):
  """OGame parser."""

  def __init__(self, country, universe, email, password):
    self._scraper = scraper.Scraper(country, universe, email, password)
    self._scraper.login()
    self._player = player_pb2.Player()

  def print_debug(self):
    print self._player

  def parse_all(self):
    self._scraper.clear_cache()
    self._player.timestamp = int(time.time())
    self.scrape_universe()
    self.scrape_identity()
    self.scrape_scores()
    self.scrape_officers()
    self.scrape_research()
    planets = self.scrape_planet_list()
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

  def scrape_universe(self):
    bs = self._scraper.get_page('overview')
    metas = bs.find_all('meta')
    self._player.universe.name = _get_meta(bs, 'ogame-universe-name')
    self._player.universe.speed = int(_get_meta(bs, 'ogame-universe-speed'))
    self._player.universe.fleet_speed = int(
        _get_meta(bs, 'ogame-universe-speed-fleet'))
    self._player.universe.donut_galaxy = bool(int(
        _get_meta(bs, 'ogame-donut-galaxy')))
    self._player.universe.donut_system = bool(int(
        _get_meta(bs, 'ogame-donut-system')))

  def scrape_identity(self):
    bs = self._scraper.get_page('overview')
    self._player.identity.player_id = int(_get_meta(bs, 'ogame-player-id'))
    self._player.identity.name = _get_meta(bs, 'ogame-player-name')
    alliance_id, alliance_tag, alliance_name = map(
        lambda x: _get_meta(bs, 'ogame-alliance-' + x), ('id', 'tag', 'name'))
    if alliance_id: self._player.identity.alliance_id = int(alliance_id)
    if alliance_tag: self._player.identity.alliance_tag = alliance_tag
    if alliance_name: self._player.identity.alliance_name = alliance_name

  def scrape_scores(self):
    bs = self._scraper.get_page('highscore')
    row = bs.find(class_='myrank')
    self._player.score.points = _parse(row.find(class_='score').string)
    self._player.score.rank = _parse(row.find(class_='position').string)
    self._player.score.honorific_points = _parse(list(
        row.find(class_='honorScore').stripped_strings)[1])
    self._player.score.num_players = int(bs.find(
        class_='changeSite').contents[-2].string.split('-')[1])

  def scrape_officers(self):
    bs = self._scraper.get_page('overview')
    officers = bs.find(id='officers')

    def set_officer(name):
      officer = officers.find(class_=name)
      self._player.officers.__setattr__('has_' + name, 'on' in officer['class'])

    set_officer('commander')
    set_officer('admiral')
    set_officer('engineer')
    set_officer('geologist')
    set_officer('technocrat')

  def scrape_research(self):
    bs = self._scraper.get_page('research')
    for label, name in {
      'research113': 'energy',
      'research120': 'laser',
      'research121': 'ion',
      'research114': 'hyperspace',
      'research122': 'plasma',
      'research106': 'espionage',
      'research108': 'computer',
      'research124': 'astrophysics',
      'research123': 'intergalactic_network',
      'research199': 'graviton',
      'research115': 'combustion_drive',
      'research117': 'impulse_drive',
      'research118': 'hyperspace_drive',
      'research109': 'weapons',
      'research110': 'shielding',
      'research111': 'armor',
    }.iteritems():
      _set_level(bs, label, self._player.research, name, is_class=True)

  def scrape_planet_list(self):
    bs = self._scraper.get_page('overview')
    planet_list = bs.find(id='planetList')
    planets = []
    for planet in planet_list.find_all(class_='smallplanet'):
      planet_id = planet['id'].split('-')[1]
      moon = planet.find(class_='moonlink')
      moon_id = moon['href'].split('=')[-1] if moon else None
      planets.append((planet_id, moon_id))
    return planets

  def scrape_planet(self, planet_id, planet):
    planet.id = int(planet_id)
    self.scrape_planet_details(planet_id, planet)
    self.scrape_resources(planet_id, planet)
    self.scrape_mines(planet_id, planet)
    self.scrape_production_rates(planet_id, planet)
    self.scrape_facilities(planet_id, planet)
    self.scrape_shipyard(planet_id, planet)
    self.scrape_defense(planet_id, planet)

  def scrape_planet_details(self, planet_id, planet):
    bs = self._scraper.get_page('overview', planet_id)
    planet.name = _get_meta(bs, 'ogame-planet-name')
    coords = _get_meta(bs, 'ogame-planet-coordinates')
    parts = coords.split(':')  # e.g. [2:349:10]
    (planet.coordinates.galaxy,
     planet.coordinates.system,
     planet.coordinates.position) = map(int, parts)

    # Find the diameter and temperature in the planet tooltip.
    if not planet.is_moon:
      bs_title = bs4.BeautifulSoup(
          bs.find(class_='smallplanet', id='planet-' + planet_id).a['title'],
          'lxml')
      strings = list(bs_title.stripped_strings)
      diameter, temperature = strings[1], strings[2]
      r = re.search(r'^([0-9\.]+)km \(([0-9\.]+)/([0-9\.]+)\)$', diameter)
      planet.diameter_km, planet.size, planet.capacity = map(
          lambda i: _parse(r.group(i)), (1, 2, 3))
      r = re.search(r'^(-?[0-9\s]+)\xb0C.*(-?[0-9\s]+)\xb0C$', temperature)
      planet.min_temperature, planet.max_temperature = map(
          lambda i: _parse(r.group(i)), (1, 2))

    # For moons we need to look at the raw javascript.
    # E.g. "6.164km (<span>7<\/span>\/<span>10<\/span>)"
    else:
      for script in bs.find_all('script'):
        r_diameter = re.search(
            r'([0-9\.]+)km[^0-9]+([0-9]+)[^0-9]*/[^0-9]*([0-9]+)',
            script.__str__())
        if not r_diameter: continue
        r_temperature = re.search(r'(-?[0-9\s]+)\\u00b0C.*(-?[0-9\s]+)\\u00b0C',
                                  script.__str__())
        if not r_temperature: continue
        planet.diameter_km, planet.size, planet.capacity = map(
            lambda i: _parse(r_diameter.group(i)), (1, 2, 3))
        planet.min_temperature, planet.max_temperature = map(
            lambda i: _parse(r_temperature.group(i)), (1, 2))
        break

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

  def scrape_production_rates(self, planet_id, planet):
    bs = self._scraper.get_page('resourceSettings', planet_id)
    selects = bs.find_all('select')

    def set_rate(name, dest):
      select = [select for select in selects if select.get('name') == name][0]
      selected = [option for option in select.find_all('option')
                  if option.get('selected') is not None][0]
      planet.production_rates.__setattr__(dest, float(selected['value']) / 100.)

    set_rate('last1', 'metal')
    set_rate('last2', 'crystal')
    set_rate('last3', 'deuterium')
    set_rate('last4', 'solar_plant')
    set_rate('last12', 'fusion_reactor')
    set_rate('last212', 'solar_satellites')

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
