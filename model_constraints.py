import shutil
import sys
import os.path
import pandas as pd
import numpy as np
import pyomo.environ as env
import ast
from pyomo.environ import *
import networkx as nx

# import other water tap modules
import get_graph_chars
import watertap as wt


# LINKS COMING OUT OF SOURCE NODE AND GOING INTO FIRST UP MUST EQUAL FEEDWATER TOTAL! 
def source_flow_constraint(m, source_node, variable, G): #RENAME THIS CONSTRAINT  
    
    link_variable = wt.get_model_chars.get_link_variable(m, variable)
    
    sum_of_inflows = 0
    for link in G.out_edges(source_node):
        sum_of_inflows = sum_of_inflows + link_variable[G.edges[link]['name']]

    max_flow_in = G.nodes[source_node][variable]
        
    return sum_of_inflows == max_flow_in


# SOURCE FLOW MASS BALANCE
def node_mass_balance_constraint(m, node, variable, G):
    
    link_variable = wt.get_model_chars.get_link_variable(m, variable)
    
    flow_in = 0
    for edge in G.in_edges(node):
        flow_in = flow_in + link_variable[G.edges[edge]['name']]
    flow_out = 0
    for edge in G.out_edges(node):
        flow_out = flow_out + link_variable[G.edges[edge]['name']]

    return (-0.000000001, flow_in - flow_out, 0.000000001)


#### GET EQUATION FOR OUTFLOWS OF UNIT PROCESS ####
def get_up_treatment_equation(m, unit_process, up_edge, variable, G):
    
    up = wt.module_import.get_module(G.edges[up_edge]['treatment_name'])
    link_variable = wt.get_model_chars.get_link_variable(m, variable)
    
    link_variable_wname = link_variable[G.edges[up_edge]['name']]
    
    if variable == 'Flow':
        return up.flow_treatment_equation(m, G, link_variable_wname)
    if variable == 'TOC':
        return up.toc_treatment_equation(m, G, link_variable_wname)
    if variable == 'Nitrate':
        return up.nitrate_treatment_equation(m, G, link_variable_wname)
    if variable == 'TDS':
        return up.tds_treatment_equation(m, G, link_variable_wname, up_edge)
    

# NEW WITH UNIT PROCESS #
# recovered stream from unit process
def calculate_recovered_streams(m, unit_process, variable, G):
    
    sum_of_treated_flow = get_sum_of_up_outflow(m, unit_process, 'use_stream', variable, G)
    
    start_node = ('%s_start' % unit_process)
    end_node = ('%s_end' % unit_process)
    up_edge = (start_node, end_node)
    
    treated_flow = get_up_treatment_equation(m, unit_process, up_edge, variable, G)

    return sum_of_treated_flow == treated_flow


def get_sum_of_up_outflow(m, unit_process, link_type, variable, G):
    
    link_variable = wt.get_model_chars.get_link_variable(m, variable)
    
    sum_of_outflow = 0
    for edge in G.out_edges(('%s_end' % unit_process)):
        if G.edges[edge]['type'] == link_type:
            sum_of_outflow = sum_of_outflow + link_variable[G.edges[edge]['name']]
    
    return sum_of_outflow


# DO THIS NEXT ---> THIS IS ONLY RECYCLING FRACTION OF WASTE --> NEED TO ADD RECYCLE OF TREATED STREAM.
def max_recycle_streams(m, unit_process, variable, G):
        
    sum_of_recycle_flow = get_sum_of_up_outflow(m, unit_process, 'recycle_stream', variable, G)
    link_variable = wt.get_model_chars.get_link_variable(m, variable)
    
    start_node = ('%s_start' % unit_process)
    end_node = ('%s_end' % unit_process)
    up_edge = (start_node, end_node)
    up = wt.module_import.get_module(G.edges[up_edge]['treatment_name'])
    
    if sum_of_recycle_flow is 0:
        return Constraint.Skip
    else:
        
        recycle_factor = G.edges[up_edge]['recycle_factor']
        
        sum_of_feedwater = 0

        for edge in G.in_edges('%s_source_and_recycle' % unit_process):
            if G.edges[edge]['type'] == 'feedwater_stream':
                sum_of_feedwater = sum_of_feedwater + link_variable[G.edges[edge]['name']]

        #print('RECYCLE FACTOR:', recycle_factor)
        
        if variable == 'Flow':
            return sum_of_recycle_flow == sum_of_feedwater * recycle_factor
        else:
            if variable == 'TOC':
                treated_flow = up.toc_treatment_equation(m, G, sum_of_feedwater)
            if variable == 'Nitrate':
                treated_flow = up.nitrate_treatment_equation(m, G, sum_of_feedwater) 
            if variable == 'TDS':
                treated_flow = up.tds_treatment_equation(m, G, sum_of_feedwater) 
            return sum_of_recycle_flow == treated_flow * recycle_factor
        
        
        
        
#THIS IS FOR END NODE!!!!! BETTER NAMING NEEDED FOR FUNCTIONS ---> PROBABLY DON'T NEED THIS -> JUST OPTIMIZE FOR USE STREAMS!
def calculate_recovered_water(m, end_node, G): # AT NODE
    
    #print(end_node)
    
    recovered_flow = 0; 
    for up_outflow_link in G.in_edges(end_node): # TO DO MAKE FUNCTION
        recovered_flow = recovered_flow + m.FlowInLinkSegments[G.edges[up_outflow_link]['name']]
    
    return m.RecoveredFlow[end_node] == recovered_flow


#THIS IS FOR END NODE!!!!! BETTER NAMING NEEDED FOR FUNCTIONS ---> PROBABLY DON'T NEED THIS -> JUST OPTIMIZE FOR USE STREAMS!
def calculate_total_train_cost(m, end_node, G): # AT NODE
    
    #print(end_node)
    
    total_cost_at_use = 0
    
    for unit_process in wt.get_graph_chars.get_unit_process_name_list(G):

        up_start_node = ('%s_start' % unit_process)
        up_end_node = ('%s_end' % unit_process)
        up_edge = (up_start_node, up_end_node)

        up_cost = m.TotalCostInLinkSegments[G.edges[up_edge]['name']]

        total_cost_at_use = total_cost_at_use + up_cost

    return m.RecoveredCost[end_node] == total_cost_at_use


def calculate_levelized_cost(m, end_node):
    return m.LevelizedCost[end_node] == m.RecoveredCost[end_node] / m.RecoveredFlow[end_node]


# NEW WITH UNIT PROCESS #
# recovered stream from unit process # CHANGE UNIT PROCESS TO UNIT PROCESS NAME
def calculate_up_total_costs(m, unit_process, G, cost_method):
    
    #print(unit_process)
    
    start_node = ('%s_start' % unit_process)
    end_node = ('%s_end' % unit_process)
    up_edge = (start_node, end_node)
    
    up = wt.module_import.get_module(G.edges[up_edge]['treatment_name'])
    
    flow_in = m.FlowInLinkSegments[G.edges[up_edge]['name']]
    
    if 'mem_manu' in G.edges[up_edge]:
        mem_manu = G.edges[up_edge]['mem_manu']
        mem_model_type = G.edges[up_edge]['mem_model_type']
    else:
        mem_manu = None
        mem_model_type = None
        
    if mem_manu is not None:
        return m.TotalCostInLinkSegments[G.edges[up_edge]['name']] == up.total_up_cost(m=m, flow_in = flow_in, G = G,
                                                                                       cost_method = cost_method,
                                                                                      mem_manu = mem_manu,
                                                                                      mem_model_type = mem_model_type,
                                                                                      up_edge = up_edge)
    
    else:
        return m.TotalCostInLinkSegments[G.edges[up_edge]['name']] == up.total_up_cost(flow_in = flow_in, G = G,
                                                                               cost_method = cost_method)
      




def main():
    print("importing something")
    # need to define anything here?

if __name__ == "__main__":
    main()