import numpy as np
import pandas as pd
import datetime
import time
import matplotlib.pyplot as plt
from multiprocessing import Pool
import multiprocessing
import os, sys

# inflow consituents must be lower than constraint otherwise 0 flow into UP

recovery_factor = 0.99
BOD_constraint = 250
TOC_constraint = 150


def get_edge_info(unit_process_name):
    start_node = ('%s_start' % unit_process_name)
    end_node = ('%s_end' % unit_process_name)
    edge = (start_node, end_node)
    return start_node, end_node, edge

def add_recovery_attribute(G, unit_process, unit_process_name):
    
    start_node, end_node, edge = get_edge_info(unit_process_name)
    print('edge', edge)
    G.edges[edge]['recovery_factor'] = recovery_factor
    
    #G.nodes[unit_process_name]['recovery_factor'] = recovery_factor
    
    return G

def add_BOD_inlet_constraint(G, unit_process, unit_process_name):
    start_node, end_node, edge = get_edge_info(unit_process_name)
    G.edges[edge]['BOD_constraint'] = BOD_constraint
    return G

def add_TOC_inlet_constraint(G, unit_process, unit_process_name):
    start_node, end_node, edge = get_edge_info(unit_process_name)
    G.edges[edge]['TOC_constraint'] = TOC_constraint
    return G

def add_recycle_and_waste_attribute(G, unit_process, unit_process_name, recyle_fraction_of_waste=None):
    
    start_node, end_node, edge = get_edge_info(unit_process_name)
    
    if recyle_fraction_of_waste is None: 
        G.edges[edge]['recycle_factor'] = 0
        G.edges[edge]['waste_factor'] = 1 - recovery_factor
    else:
        G.edges[edge]['recycle_factor'] = (1 - recovery_factor) * (recyle_fraction_of_waste)
        G.edges[edge]['waste_factor'] = 1 - recovery_factor - G.edges[edge]['recycle_factor']
    
    return G


def main():
    print("importing something")
    # need to define anything here?

if __name__ == "__main__":
    main()