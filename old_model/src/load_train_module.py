import shutil
import sys
import os.path
import pandas as pd
import numpy as np
import itertools
import ast
import networkx as nx


def load_edges(G, df):

    df = df[df.type == "edge"]
    list_of_edges = []
    df = df.reset_index()
    for row in range(0, len(df)):
        list_of_edges.append(
            (
                df.start_node_list[row],
                df.end_node_list[row],
                ast.literal_eval(df.data_list[row]),
            )
        )

    G.add_edges_from(list_of_edges)

    return G


def load_nodes(G, df):

    df = df[df.type == "node"]
    del df["start_node_list"]
    del df["end_node_list"]
    df = df.reset_index()
    for row in range(0, len(df)):
        for key in ast.literal_eval(df.data_list[row]).keys():
            G.nodes[df.node_name_list[row]][key] = ast.literal_eval(df.data_list[row])[
                key
            ]

    return G


def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()
