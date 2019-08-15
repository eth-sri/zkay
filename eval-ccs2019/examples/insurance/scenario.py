import os

from examples.scenarios import ScenarioGenerator

script_dir = os.path.dirname(os.path.realpath(__file__))

g = ScenarioGenerator(script_dir, 'insurance.sol', {'insurance': 10, 'police': 20, 'client1': 30})

# run functions
g.run_function('constructor', 'insurance', ['police'])
g.run_function('register', 'client1', [])
g.run_function('insure_item', 'client1', [1000, 10])
g.run_function('insure_item', 'client1', [2000, 20])
g.run_function('retract_item', 'client1', [0])
g.run_function('accept_item', 'insurance', ['client1', 1])
g.run_function('set_stolen', 'police', ['client1', 1, True])
g.run_function('set_broken', 'police', ['client1', 1, False])
g.run_function('get_refund', 'client1', [1])

g.finalize()
