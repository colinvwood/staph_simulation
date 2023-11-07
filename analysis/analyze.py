import glob
import json
import logging
import os
import sys

import pandas as pd

from .Analysis import Analysis

logging.getLogger().setLevel(logging.INFO)


def calc_proportions(df):
    proportions = pd.DataFrame()
    for stat in df.columns:
        proportions[f'{stat} correct'] = [sum(df[stat] == 1) / len(df[stat])]
        proportions[f'{stat} reverse'] = [sum(df[stat] == -1) / len(df[stat])]
        proportions[f'{stat} ambiguous'] = [sum(df[stat] == 0) / len(df[stat])]

    return proportions


# python -m analysis.analyze analysis_params.json
if __name__ == "__main__":
    analysis_params_file = sys.argv[1]

    with open(analysis_params_file, 'r') as file:
        analysis_params = json.load(file)

    sim_params_file = analysis_params["path to simulation parameters"]
    with open(sim_params_file, "r") as file:
        sim_params = json.load(file)

    # find all population files belonging to simulation
    pop_files_dir = analysis_params["path to simulation files"]
    sim_id = sim_params["run_id"]
    pop_files_pattern = os.path.join(
        pop_files_dir, "run_" + str(sim_id) + "*pop*csv"
    )
    pop_files = glob.glob(pop_files_pattern)
    source_pop_files = [file for file in pop_files if "source" in file]
    recipient_pop_files = [file for file in pop_files if "recipient" in file]

    # ensure files from matching simulation runs are analyzed together
    source_pop_files.sort()
    recipient_pop_files.sort()

    # perform analyses
    all_proportions = []
    sim_count = 0
    for source_pop, recipient_pop in zip(
        source_pop_files, recipient_pop_files
    ):
        sim_count += 1
        logging.info(f"simulation repetition: {sim_count}")

        analysis_params["source population file"] = source_pop
        analysis_params["recipient population file"] = recipient_pop

        sim_results = pd.DataFrame()
        for rep in range(analysis_params["analysis repetitions"]):
            logging.info(f"\tanalysis repetition: {rep + 1}")
            analysis = Analysis.from_params(analysis_params)
            analysis.perform_analysis()
            rep_results = analysis.results
            sim_results = pd.concat([sim_results, rep_results])

        all_proportions.append(calc_proportions(sim_results))

    filename = (
        f"src{sim_params['source generations']}-"
        f"rec{sim_params['recipient generations']}-"
        f"bot{sim_params['bottleneck']}-"
        f"cmb{analysis_params['combination number']}"
        ".json"
    )
    pd.concat(all_proportions, ignore_index=True).to_json(
        filename, orient='records'
    )
