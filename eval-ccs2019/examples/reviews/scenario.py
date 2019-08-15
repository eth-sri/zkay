import os

from examples.scenarios import ScenarioGenerator

script_dir = os.path.dirname(os.path.realpath(__file__))

g = ScenarioGenerator(script_dir, 'reviews.sol', {'pc': 10, 'r1': 20, 'r2': 30, 'r3': 40, 'author': 100})

# run functions
g.run_function('constructor', 'pc', ['r1', 'r2', 'r3'])
g.run_function('registerPaper', 'author', [1234])
g.run_function('recordReview', 'r1', [1234, 4])
g.run_function('recordReview', 'r2', [1234, 2])
g.run_function('recordReview', 'r3', [1234, 1])
g.run_function('decideAcceptance', 'pc', ['author'])

g.finalize()
