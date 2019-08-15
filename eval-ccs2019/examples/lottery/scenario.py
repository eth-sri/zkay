import os

from examples.scenarios import ScenarioGenerator

script_dir = os.path.dirname(os.path.realpath(__file__))

g = ScenarioGenerator(script_dir, 'lottery.sol', {'master': 10, 'x': 20, 'y': 30})

# run functions
g.run_function('constructor', 'master', [1234])
g.run_function('bet', 'x', [1234])
g.run_function('bet', 'y', [1235])
g.run_function('publish_secret', 'master', [])
g.run_function('claim_winner', 'x', [])

g.finalize()
