from pylab import *
import shutil
import sys
import os.path
import pandas as pd
import numpy as np
import networkx as nx


def remove(G, process_name):
    G.remove_node(process_name)
    return G

def remove_single_process(G, process_name):
    
    remove_list = []
    for edge in G.edges(): #change this to processes list only - this could take longer if there are many nodes.
        if (G.edges[edge]['name'] == process_name): # & (node != process_name)): 
            remove_list = [('%s_start' % process_name), ('%s_end' % process_name)]
    
    G.remove_nodes_from(remove_list)
    
    remove_list = []
    for node in G.nodes():
            if len(G.in_edges(node)) == 0:
                if len(G.out_edges(node)) == 0:
                    remove_list.append(node)
    
    G.remove_nodes_from(remove_list)
    
    return G

def select_multiple_processes(G, process_name_list):
    
    remove_list = []
    for node in G.nodes(): #change this to processes list only - this could take longer if there are many nodes.
        if (G.nodes[node]['type'] == 'treatment_process'): # & (node != process_name)): 
            if node not in process_name_list: 
                remove_list.append(node)
    
    G.remove_nodes_from(remove_list)
    
    return G










def main():
    print("importing something")
    # need to define anything here?

if __name__ == "__main__":
    main()

    
    
    
    