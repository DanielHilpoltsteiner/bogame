import re
import sys
import threading
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


def _validate_inputs(country, universe, email, password):
  if not country:
    return 'No country selected'
  if not universe:
    return 'No universe entered'
  if not email:
    return 'No email address entered'
  if not password:
    return 'No password entered'
  try:
    universe = int(universe)
  except ValueError:
    return 'Universe should be in 1...199'
  if not 0 < universe < 200:
    return 'Universe should be in 1...199'
  if not re.match(
      r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$',
      email):
    return 'Invalid email address'


class Parser(object):
  """OGame parser."""

  def __init__(self, country, universe, email, password):
    error = _validate_inputs(country, universe, email, password)
    if error:
      raise ValueError(error)
    self._scraper = scraper.Scraper(country, universe, email, password)
    self._scraper.login()
    self._player = player_pb2.Player()
    self._parse_stage = ''

  def parse_all(self):
    self._scraper.clear_cache()
    self._player.timestamp = int(time.time())

    self._parse_stage = 'Scraping player info...'

    universe = player_pb2.Universe()
    t_universe = threading.Thread(target=self._scrape_universe,
                                  args=(universe,))
    t_universe.start()

    identity = player_pb2.Identity()
    t_identity = threading.Thread(target=self._scrape_identity,
                                  args=(identity,))
    t_identity.start()

    scores = player_pb2.Score()
    t_scores = threading.Thread(target=self._scrape_scores, args=(scores,))
    t_scores.start()

    officers = player_pb2.Officers()
    t_officers = threading.Thread(target=self._scrape_officers,
                                  args=(officers,))
    t_officers.start()

    research = player_pb2.Research()
    t_research = threading.Thread(target=self._scrape_research,
                                  args=(research,))
    t_research.start()

    t_universe.join()
    t_identity.join()
    t_scores.join()
    t_officers.join()
    t_research.join()
    self._player.universe.CopyFrom(universe)
    self._player.identity.CopyFrom(identity)
    self._player.score.CopyFrom(scores)
    self._player.officers.CopyFrom(officers)
    self._player.research.CopyFrom(research)

    planets = self._scrape_planet_list()
    for i, pair in enumerate(planets):
      planet_id, moon_id = pair
      planet = self._player.planets.add()
      if i == 0:
        planet.is_homeworld = True
      self._parser_stage = 'Scraping planet {}...'.format(planet_id)
      self._scrape_planet(planet_id, planet)
      if moon_id:
        planet.moon.is_moon = True
        planet.moon.coordinates.CopyFrom(planet.coordinates)
        self._parser_stage = 'Scraping moon {}...'.format(planet_id)
        self._scrape_planet(moon_id, planet.moon)

    self._parse_stage = 'Completed'

  def get_player(self):
    return self._player

  def get_parse_stage(self):
    return self._parse_stage

  def _scrape_universe(self, universe):
    bs = self._scraper.get_page('overview')
    metas = bs.find_all('meta')
    universe.name = _get_meta(bs, 'ogame-universe-name')
    universe.speed = int(_get_meta(bs, 'ogame-universe-speed'))
    universe.fleet_speed = int(
        _get_meta(bs, 'ogame-universe-speed-fleet'))
    universe.donut_galaxy = bool(int(
        _get_meta(bs, 'ogame-donut-galaxy')))
    universe.donut_system = bool(int(
        _get_meta(bs, 'ogame-donut-system')))

  def _scrape_identity(self, identity):
    bs = self._scraper.get_page('overview')
    identity.player_id = int(_get_meta(bs, 'ogame-player-id'))
    identity.name = _get_meta(bs, 'ogame-player-name')
    alliance_id, alliance_tag, alliance_name = map(
        lambda x: _get_meta(bs, 'ogame-alliance-' + x), ('id', 'tag', 'name'))
    if alliance_id: self._player.identity.alliance_id = int(alliance_id)
    if alliance_tag: self._player.identity.alliance_tag = alliance_tag
    if alliance_name: self._player.identity.alliance_name = alliance_name

  def _scrape_scores(self, scores):
    bs = self._scraper.get_page('highscore')
    row = bs.find(class_='myrank')
    scores.points = _parse(row.find(class_='score').string)
    scores.rank = _parse(row.find(class_='position').string)
    scores.honorific_points = _parse(list(
        row.find(class_='honorScore').stripped_strings)[1])
    scores.num_players = int(bs.find(
        class_='changeSite').contents[-2].string.split('-')[1])

  def _scrape_officers(self, officers):
    bs = self._scraper.get_page('overview')
    officers_element = bs.find(id='officers')

    def set_officer(name):
      officer = officers_element.find(class_=name)
      officers.__setattr__('has_' + name, 'on' in officer['class'])

    set_officer('commander')
    set_officer('admiral')
    set_officer('engineer')
    set_officer('geologist')
    set_officer('technocrat')

  def _scrape_research(self, research):
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
      _set_level(bs, label, research, name, is_class=True)

  def _scrape_planet_list(self):
    bs = self._scraper.get_page('overview')
    planet_list = bs.find(id='planetList')
    planets = []
    for planet in planet_list.find_all(class_='smallplanet'):
      planet_id = planet['id'].split('-')[1]
      moon = planet.find(class_='moonlink')
      moon_id = moon['href'].split('=')[-1] if moon else None
      planets.append((planet_id, moon_id))
    return planets

  def _scrape_planet(self, planet_id, planet):
    planet.id = int(planet_id)

    planet_details = player_pb2.Planet()
    planet_details.CopyFrom(planet)
    t_planet_details = threading.Thread(target=self._scrape_planet_details,
                                        args=(planet_id, planet_details))
    t_planet_details.start()
    resources = player_pb2.Resources()
    t_resources = threading.Thread(target=self._scrape_resources,
                                   args=(planet_id, resources))
    t_resources.start()
    mines = player_pb2.Mines()
    t_mines = threading.Thread(target=self._scrape_mines,
                               args=(planet_id, mines))
    t_mines.start()
    production_rates = player_pb2.ProductionRates()
    t_production_rates = threading.Thread(target=self._scrape_production_rates,
                                          args=(planet_id, production_rates))
    t_production_rates.start()
    facilities = player_pb2.Facilities()
    t_facilities = threading.Thread(
        target=self._scrape_moon_facilities if planet.is_moon
               else self._scrape_planet_facilities,
        args=(planet_id, facilities))
    t_facilities.start()
    shipyard = player_pb2.Shipyard()
    t_shipyard = threading.Thread(target=self._scrape_shipyard,
                                  args=(planet_id, shipyard))
    t_shipyard.start()
    defense = player_pb2.Defense()
    t_defense = threading.Thread(target=self._scrape_defense,
                                 args=(planet_id, defense))
    t_defense.start()

    t_planet_details.join()
    t_resources.join()
    t_mines.join()
    t_production_rates.join()
    t_facilities.join()
    t_shipyard.join()
    t_defense.join()

    planet.CopyFrom(planet_details)
    if resources.ByteSize():
      planet.resources.CopyFrom(resources)
    if mines.ByteSize():
      planet.mines.CopyFrom(mines)
    if production_rates.ByteSize():
      planet.production_rates.CopyFrom(production_rates)
    if facilities.ByteSize():
      planet.facilities.CopyFrom(facilities)
    if shipyard.ByteSize():
      planet.shipyard.CopyFrom(shipyard)
    if defense.ByteSize():
      planet.defense.CopyFrom(defense)


  def _scrape_planet_details(self, planet_id, planet):
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
      r = re.search(r'^(-?[0-9\s]+)\xb0C[^0-9-]*(-?[0-9\s]+)\xb0C$',
                    temperature)
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

  def _scrape_resources(self, planet_id, resources):
    bs = self._scraper.get_page('overview', planet_id)
    resources.metal = _get_resource(bs, 'metal')
    resources.crystal = _get_resource(bs, 'crystal')
    resources.deuterium = _get_resource(bs, 'deuterium')
    resources.energy = _get_resource(bs, 'energy')
    resources.dark_matter = _get_resource(bs, 'darkmatter')

  def _scrape_mines(self, planet_id, mines):
    bs = self._scraper.get_page('resources', planet_id)
    _set_level(bs, 'button1', mines, 'metal')
    _set_level(bs, 'button2', mines, 'crystal')
    _set_level(bs, 'button3', mines, 'deuterium')
    _set_level(bs, 'button4', mines, 'solar_plant')
    _set_level(bs, 'button5', mines, 'fusion_reactor')
    _set_level(bs, 'button7', mines, 'metal_storage')
    _set_level(bs, 'button8', mines, 'crystal_storage')
    _set_level(bs, 'button9', mines, 'deuterium_storage')

  def _scrape_production_rates(self, planet_id, production_rates):
    bs = self._scraper.get_page('resourceSettings', planet_id)
    selects = bs.find_all('select')

    def set_rate(name, dest):
      select = [select for select in selects if select.get('name') == name][0]
      selected = [option for option in select.find_all('option')
                  if option.get('selected') is not None][0]
      production_rates.__setattr__(dest, float(selected['value']) / 100.)

    set_rate('last1', 'metal')
    set_rate('last2', 'crystal')
    set_rate('last3', 'deuterium')
    set_rate('last4', 'solar_plant')
    set_rate('last12', 'fusion_reactor')
    set_rate('last212', 'solar_satellites')

  def _scrape_planet_facilities(self, planet_id, facilities):
    bs = self._scraper.get_page('station', planet_id)
    _set_level(bs, 'button0', facilities, 'robotics_factory')
    _set_level(bs, 'button1', facilities, 'shipyard')
    _set_level(bs, 'button2', facilities, 'research_lab')
    _set_level(bs, 'button3', facilities, 'alliance_depot')
    _set_level(bs, 'button4', facilities, 'missile_silo')
    _set_level(bs, 'button5', facilities, 'nanite_factory')
    _set_level(bs, 'button6', facilities, 'terraformer')
    _set_level(bs, 'button7', facilities, 'space_dock')

  def _scrape_moon_facilities(self, planet_id, facilities):
    bs = self._scraper.get_page('station', planet_id)
    _set_level(bs, 'button0', facilities, 'robotics_factory')
    _set_level(bs, 'button1', facilities, 'shipyard')
    _set_level(bs, 'button2', facilities, 'lunar_base')
    _set_level(bs, 'button3', facilities, 'sensor_phalanx')
    _set_level(bs, 'button4', facilities, 'jump_gate')

  def _scrape_shipyard(self, planet_id, shipyard):
    bs = self._scraper.get_page('shipyard', planet_id)
    battleships = bs.find(id='battleships')
    _set_level(battleships, 'button1', shipyard, 'light_fighters')
    _set_level(battleships, 'button2', shipyard, 'heavy_fighers')
    _set_level(battleships, 'button3', shipyard, 'cruisers')
    _set_level(battleships, 'button4', shipyard, 'battleships')
    _set_level(battleships, 'button5', shipyard, 'battlecruisers')
    _set_level(battleships, 'button6', shipyard, 'bombers')
    _set_level(battleships, 'button7', shipyard, 'destroyers')
    _set_level(battleships, 'button8', shipyard, 'deathstars')
    civilships = bs.find(id='civilships')
    _set_level(civilships, 'button1', shipyard, 'small_cargos')
    _set_level(civilships, 'button2', shipyard, 'large_cargos')
    _set_level(civilships, 'button3', shipyard, 'colony_ships')
    _set_level(civilships, 'button4', shipyard, 'recyclers')
    _set_level(civilships, 'button5', shipyard, 'espionage_probes')
    _set_level(civilships, 'button6', shipyard, 'solar_satellites')

  def _scrape_defense(self, planet_id, defense):
    bs = self._scraper.get_page('defense', planet_id)
    _set_level(bs, 'defense1', defense, 'rocker_launchers')
    _set_level(bs, 'defense2', defense, 'light_lasers')
    _set_level(bs, 'defense3', defense, 'heavy_lasers')
    _set_level(bs, 'defense4', defense, 'gauss_canons')
    _set_level(bs, 'defense5', defense, 'ion_canons')
    _set_level(bs, 'defense6', defense, 'plasma_turrets')
    _set_level(bs, 'defense7', defense, 'has_small_shield_dome')
    _set_level(bs, 'defense8', defense, 'has_large_shield_dome')
    _set_level(bs, 'defense9', defense, 'anti_ballistic_missiles')
    _set_level(bs, 'defense10', defense, 'interplanetary_missiles')
