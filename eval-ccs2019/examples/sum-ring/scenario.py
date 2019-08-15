import os

from examples.scenarios import ScenarioGenerator

script_dir = os.path.dirname(os.path.realpath(__file__))

g = ScenarioGenerator(script_dir, 'sum-ring.sol', {'p1': 10, 'p2': 20, 'p3': 30})

# run functions
g.run_function('constructor', 'p1', [12345])
g.run_function('addVal', 'p1', [100, 'p2'])
g.run_function('addVal', 'p2', [200, 'p3'])
g.run_function('addVal', 'p3', [300, 'p1'])
g.run_function('evaluateSum', 'p1', [])

g.finalize()
