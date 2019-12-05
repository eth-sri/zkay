import os
import sys
import importlib
from typing import List, Tuple

from zkay.examples.scenario import Scenario

examples_dir = os.path.dirname(os.path.abspath(__file__))
scenario_dir = os.path.join(examples_dir, 'scenarios')


def collect_scenarios(directory: str):
    scenario: List[Tuple[str, Scenario]] = []

    sys.path.append(directory)
    for f in os.listdir(directory):
        if f.endswith(".py"):
            p = importlib.import_module(f[:-3])
            s = p.SCENARIO.with_root(examples_dir)
            scenario.append((s.name(), s))
            del p
    sys.path.pop()
    return scenario


all_scenarios = collect_scenarios(scenario_dir)
