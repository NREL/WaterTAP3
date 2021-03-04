import numpy as np
import pandas as pd
import datetime
import time
import matplotlib.pyplot as plt
from multiprocessing import Pool
import multiprocessing
import os, sys


def feedwater(
    input_file=None,
    reference=None,
    water_type=None,
    case_study=None,
    source_or_use=None,
    scenario=None,
):
    # TO DO: add file type for imports,
    df = pd.read_csv(input_file, index_col='variable')

    # TO DO: add options for None, add option to mask if a list is given.
    if reference is not None:
        df = df[df.reference == reference]

    if water_type is not None:
        if isinstance(water_type, list):
            pass
        else:
            df = df[df.water_type == water_type]

    if case_study is not None:
        df = df[df.case_study == case_study]

    if source_or_use is not None:
        df = df[df.source_or_use == source_or_use]
    
    if scenario is not None:
        df = df[df.scenario == scenario]

    df = df.set_index(df.index) # TODO - BE BETTER 
    df["feedwater"] = df.value
    df["SourceNodeName"] = "source_node"
    # add a verbose function that returns statements

    # ADD OPTION IF INPUT FILE IS NONE??? OR DEFINE WATER SOURCE?!?!?!?

    return df


def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()
