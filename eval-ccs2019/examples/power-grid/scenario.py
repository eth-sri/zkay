import os

from examples.scenarios import ScenarioGenerator

script_dir = os.path.dirname(os.path.realpath(__file__))

g = ScenarioGenerator(script_dir, 'power-grid.sol', {'master': 10, 'consumer': 30})

# run functions
g.run_function('constructor', 'master', [])
g.run_function('init', 'consumer', [])
g.run_function('register_consumed', 'consumer', [17])
g.run_function('declare_total', 'consumer', [])

g.finalize()
