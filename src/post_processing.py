from pylab import *

import shutil
import sys
import os.path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import write_dot, graphviz_layout

import pyomo.environ as env
import watertap as wt


def get_result_table(model, analysis_variables):
    df = pd.DataFrame()
    import pyomo.environ as env

    for variable in analysis_variables:
        link_variable = wt.get_model_chars.get_link_variable(model, variable)

        column = []
        names = []
        for x in model.LinkSet:
            column.append(round(env.value(link_variable[x]), 3))
            names.append(x)
        df[variable] = column
    df = df.set_index(np.array(names))

    return df


def get_pipeparity(model, variable):
    import pyomo.environ as env

    if variable == "levelized_cost":
        levelized_cost_sum = 0
        for x in model.RecoveredWaterNodes:
            levelized_cost_sum = levelized_cost_sum + env.value(model.LevelizedCost[x])
        return levelized_cost_sum


def get_optimization_result_table(G, model, analysis_variables, ro_membrane=False):
    df = pd.DataFrame()
    import pyomo.environ as env

    for variable in analysis_variables:
        link_variable = wt.get_model_chars.get_link_variable(model, variable)

        column = []
        names = []
        for x in model.LinkSet:
            column.append(round(env.value(link_variable[x]), 3))
            names.append(x)
        df[variable] = column
    df = df.set_index(np.array(names))

    df = df[df.Flow > 0]

    if ro_membrane == True:
        for edge in G.edges():
            if G.edges[edge]["type"] == "treatment_process":
                if G.edges[edge]["mem_manu"] is not None:
                    if (
                        env.value(model.FlowInLinkSegments[G.edges[edge]["name"]])
                        > 0.000001
                    ):
                        df["mem_manu"] = np.array(None)
                        df["mem_model_type"] = np.array(None)
                        df.at[G.edges[edge]["name"], "mem_manu"] = G.edges[edge][
                            "mem_manu"
                        ]
                        df.at[G.edges[edge]["name"], "mem_model_type"] = G.edges[edge][
                            "mem_model_type"
                        ]

    return df


def get_bar_chart(
    data=None,
    x_variable=None,
    y_variable=None,
    compare_trains=False,
    models=None,
    model_names=None,
    compare_scenario=None,
):

    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns

    if data is not None:

        data = data.copy(deep=True)

        data["link"] = data.index

        if x_variable == None:
            x_variable = "link"

        data = data[data[y_variable] > 0]

        plt.figure(figsize=(16, 6))

        if compare_scenario is None:

            figure = sns.barplot(x=x_variable, y=y_variable, data=data, color="blue")
            figure = figure.set_xticklabels(
                figure.get_xticklabels(),
                rotation=45,
                horizontalalignment="right",
                fontweight="light",
            )

        else:

            figure = sns.barplot(
                x=x_variable, y=y_variable, data=data, hue=compare_scenario, ci=None
            )
            figure = figure.set_xticklabels(
                figure.get_xticklabels(),
                rotation=45,
                horizontalalignment="right",
                fontweight="light",
            )

        return figure

    if models is not None:
        data = pd.DataFrame()
        i = 0

        analysis_variables = [y_variable]

        for model in models:
            data_hold = wt.post_processing.get_result_table(model, analysis_variables)
            data_hold["Model"] = np.array(model_names[i])

            data = pd.concat([data, data_hold])
            i = i + 1

        data["link"] = data.index

        if x_variable == None:
            x_variable = "link"

        data = data[data[y_variable] > 0]

        plt.figure(figsize=(16, 6))
        figure = sns.barplot(
            x=x_variable, y=y_variable, data=data, hue="Model", ci=None
        )
        figure = figure.set_xticklabels(
            figure.get_xticklabels(),
            rotation=45,
            horizontalalignment="right",
            fontweight="light",
        )

        return data


def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()
