import os

from examples.scenarios import ScenarioGenerator

script_dir = os.path.dirname(os.path.realpath(__file__))

g = ScenarioGenerator(script_dir, 'med-stats.sol', {'hospital': 10, 'patient1': 20, 'patient2': 30})

# run functions
g.run_function('constructor', 'hospital', [])
g.run_function('record', 'hospital', ['patient1', True])
g.run_function('record', 'hospital', ['patient2', False])
g.run_function('check', 'patient1', [True])
g.run_function('check', 'patient2', [False])

g.finalize()
