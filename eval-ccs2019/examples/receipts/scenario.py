import os

from examples.scenarios import ScenarioGenerator

script_dir = os.path.dirname(os.path.realpath(__file__))

g = ScenarioGenerator(script_dir, 'receipts.sol', {'business': 10, 'customer1': 20, 'customer2': 30})

# run functions
g.run_function('constructor', 'business', [])
g.run_function('give_receipt', 'business', [1234, 20])
g.run_function('give_receipt', 'business', [1235, 50])
g.run_function('receive_receipt', 'customer1', [1234, 20])
g.run_function('receive_receipt', 'customer2', [1235, 50])
g.run_function('check', 'business', [1234])
g.run_function('check', 'business', [1235])

g.finalize()
