"""Formula book.

Variable name conventions:
ET  =  energy technology
 L  =  level of facility
 T  =  mean temperature
US  =  universe speed
"""
import py_expression_eval

MET_ENERGY_CONSUMPTION = 'round(10 * L * (1.1 ^ L))'
CRY_ENERGY_CONSUMPTION = 'round(10 * L * (1.1 ^ L))'
DEU_ENERGY_CONSUMPTION = 'round(20 * L * (1.1 ^ L))'
SOLAR_PLANT_OUTPUT = '20 * L * (1.1 ^ L)'
FUSION_REACTOR_OUTPUT = '30 * L * (1.05 + ET * 0.01) ^ L'
FUSION_REACTOR_DEU_CONSUMPTION = '10 * L * US * (1.1 ^ L)'
SOLAR_SATELLITE_OUTPUT = '(T + 160) / 6'

_PARSER = py_expression_eval.Parser()


def F(formula, **kwargs):
  """Parse and evaluate a formula."""
  return int(_PARSER.parse(formula).evaluate(kwargs))
