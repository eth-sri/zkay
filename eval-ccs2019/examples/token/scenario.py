import os

from examples.scenarios import ScenarioGenerator

script_dir = os.path.dirname(os.path.realpath(__file__))

g = ScenarioGenerator(script_dir, 'token.sol', {'sender': 10, 'receiver': 20})

# run functions
g.run_function('constructor', 'sender', [])
g.run_function('register', 'sender', [])
g.run_function('register', 'receiver', [])
g.run_function('buy', 'sender', [1000])
g.run_function('send_tokens', 'sender', [100, 'receiver'])
g.run_function('receive_tokens', 'receiver', ['sender'])

g.finalize()
