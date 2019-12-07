import os
import sys
import importlib
from typing import List, Tuple

from zkay.examples.scenario import Scenario

examples_dir = os.path.dirname(os.path.abspath(__file__))
scenario_dir = os.path.join(examples_dir, 'scenarios')


def load_scenario(directory, filename) -> Tuple[str, Scenario]:
    sys.path.append(directory)
    p = importlib.import_module(filename[:-3])
    importlib.reload(p)
    sys.path.pop()
    s = p.SCENARIO.with_root(examples_dir)
    del p
    return s.name(), s


def collect_scenarios(directory: str):
    scenario: List[Tuple[str, Scenario]] = []
    for f in os.listdir(directory):
        if f.endswith(".py"):
            scenario.append(load_scenario(directory, f))
    return scenario


enc_scenarios = [load_scenario(scenario_dir, 'enctest.py')]
all_scenarios = collect_scenarios(scenario_dir)
