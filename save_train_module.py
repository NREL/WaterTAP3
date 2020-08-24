import shutil
import sys
import os.path
import pandas as pd
import numpy as np
import itertools
import ast
import networkx as nx


def get_edge_df(G):

    start_node_list = []
    end_node_list = []
    data_list = []
    for edge_data in G.edges(data=True):
        start_node_list.append(edge_data[0])
        end_node_list.append(edge_data[1])
        data_list.append(edge_data[2])

        df = pd.DataFrame()
        df['start_node_list'] = start_node_list
        df['end_node_list'] = end_node_list
        df['data_list'] = data_list
        df['type'] = np.array('edge')
    
    return df


def get_node_df(G):
    
    node_name_list = []; data_list = [];
    for node_data in G.nodes(data=True):
        node_name_list.append(node_data[0])
        data_list.append(node_data[1])
    
    df = pd.DataFrame()
    df['node_name_list'] = node_name_list
    df['data_list'] = data_list
    df['type'] = np.array('node')

    return df



def main():
    print("importing something")
    # need to define anything here?

if __name__ == "__main__":
    main()