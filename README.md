## Overview
This repository consists of two software modules: one to run the transmission
simulation and one to analyze the simulation results.

## Simulation Instructions
Instructions for running the simulation follow.

First, compile:

```shell
make build
```

Then, create a simulation parameters file. See the `template_sim_params.json`
file for an example.

Last, run the simulation:
```shell
./sim <simulation-parameters> <path-to-output> <random-seed> <repetitions>
```

The latter three arguments are optional and if not provided are the current
directory, the number 1, and the number 0 respectively. The `repetition`
argument is only used to uniquely name files if the simulation is being run
multiple times.

## Analysis Instructions
Instructions for running the analysis follow.

First create an analysis parameters file. See the
`template_analysis_params.json` file for an example.

Then, run the analysis:
```shell
python -m analysis.analyze analysis_params.json
```
