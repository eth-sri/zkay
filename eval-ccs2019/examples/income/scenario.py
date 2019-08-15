import os

from examples.scenarios import ScenarioGenerator

script_dir = os.path.dirname(os.path.realpath(__file__))

g = ScenarioGenerator(script_dir, 'income.sol', {'state': 10, 'me': 20})

# run functions
g.run_function('constructor', 'state', [])
g.run_function('init', 'me', [])
g.run_function('registerIncome', 'me', [1])
g.run_function('registerIncome', 'me', [40000-1])
g.run_function('checkEligibility', 'me', [])

g.finalize()
