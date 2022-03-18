# S&P 2022 Evaluation

The instructions below describe how to reproduce the experiment results of the S&P 2022 publication (ZeeStar).

## Prerequisites

As a prerequisite to run the evaluation, install the [memory-profiler](https://pypi.org/project/memory-profiler/) package as follows.

```
pip install memory_profiler
```

## Running Experiments

The example contracts (`*.zkay`) and scenarios (`scenario.py`) are provided in the `examples/` folder. Run the following command to evaluate these.

```
python ./benchmark.py examples
```

This command produces result data in the `examples/*/out/` folders.


## Creating Plots

The plots used in the publication can be reproduced from the reference results provided in `examples/*/out/` as follows.

```
# install prerequisites
pip install pandas matplotlib

# generate plots
python ./generate_plots.py
```

This command prints some statistics and produces a single PDF output file `plot.pdf`.