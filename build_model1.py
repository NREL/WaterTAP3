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

##### THIS COULD BE SET UP VERY DIFFERENTLY - > MODEL SET UP BASED ON NETWORK OR OTHER USER SET UP WITH RUN AND OPTIMIZATION 
##### IN MAIN TAB.

def build_model(G, model, cost_method = 'wt', optimize_path = False):
    
    import model_constraints as mc
    
    # SETS
    model.LinkSet = env.Set(initialize=wt.get_graph_chars.get_link_list(G)) # all links in network
    model.UnitProcesses = env.Set(initialize=wt.get_graph_chars.get_unit_process_name_list(G)) # all unit processes
    model.SourceNodes = env.Set(initialize=wt.get_graph_chars.get_source_nodes(G)) # all source nodes
    model.AllNoneSourceEndNodes = env.Set(initialize=wt.get_graph_chars.get_all_none_source_end_nodes(G))
    model.RecoveredWaterNodes = env.Set(initialize=wt.get_graph_chars.get_recovered_water_nodes(G))
        
    # VARIABLES
    model.FlowInLinkSegments = env.Var(model.LinkSet, bounds=(1e-20,None), initialize=1e-20)
    model.TOCInLinkSegments = env.Var(model.LinkSet, bounds=(1e-20,None), initialize=1e-20)
    model.NitrateInLinkSegments = env.Var(model.LinkSet, bounds=(1e-20,None), initialize=1e-20)
    model.RecoveredFlow = env.Var(model.RecoveredWaterNodes, bounds=(1e-20,None), initialize=1e-20)
    model.RecoveredCost = env.Var(model.RecoveredWaterNodes, bounds=(1e-20,None), initialize=1e-20)
    model.TotalCostInLinkSegments = env.Var(model.LinkSet, bounds=(1e-20,None), initialize=1e-20)
    model.TDSInLinkSegments = env.Var(model.LinkSet, bounds=(1e-20,None), initialize=1e-20)

    # END NODE FLOW - > FOR OPTIMIZATION LIKELY NOT NEEDEDW
    x1 = []
    
    if len(wt.get_graph_chars.get_recovered_water_nodes(G)) > 1:
        for i in range(0, len(wt.get_graph_chars.get_recovered_water_nodes(G))):
            x1.append([wt.get_graph_chars.get_recovered_water_nodes(G)[i], G])
    else:
        x1 = wt.get_graph_chars.get_recovered_water_nodes(G)
        x1.append(G)
        x1 = [x1]
    
    model.RecoveredWaterNodes2 = env.Set(initialize=x1) # all recovered water
    model.CalculateRecoveredWater = env.Constraint(model.RecoveredWaterNodes2, rule=mc.calculate_recovered_water)
    
    model.CalculateRecoveredCost = env.Constraint(model.RecoveredWaterNodes2, rule=mc.calculate_total_train_cost)    
    
    ##############################

    water_variables = ['Flow' , 'TOC', 'Nitrate'] #, 'TDS']
    x1 = []; x2 = []; x3 = [];
    for variable in water_variables:
        for i in range(0, len(wt.get_graph_chars.get_all_none_source_end_nodes(G))):
            x1.append([wt.get_graph_chars.get_all_none_source_end_nodes(G)[i], variable, G])
            
        for i in range(0, len(wt.get_graph_chars.get_source_nodes(G))):
            x2.append([wt.get_graph_chars.get_source_nodes(G)[i],  variable, G])            
            
        for i in range(0, len(wt.get_graph_chars.get_unit_process_name_list(T))):
            x3.append([wt.get_graph_chars.get_unit_process_name_list(G)[i], variable, G])     
    
    model.AllNoneSourceEndNodes2 = env.Set(initialize=x1)
    model.SourceNodes2 = env.Set(initialize=x2)
    model.UnitProcesses2 = env.Set(initialize=x3)

    # CONSTRAINTS FOR FLOW
    model.NodeMassBalanceConstraint = env.Constraint(model.AllNoneSourceEndNodes2, rule=mc.node_mass_balance_constraint)
    model.CheckUnitInletFlows = env.Constraint(model.SourceNodes2, rule=mc.source_flow_constraint)
    model.CalculateRecoveredFlows = env.Constraint(model.UnitProcesses2, rule=mc.calculate_recovered_streams)

    # RECYCLE
    model.CalculateRecycleRecoveredFlows1 = env.Constraint(model.UnitProcesses2, rule=mc.max_recycle_streams)  
    
    ## NEW CONSTRAINTS -> COST
    
    x1 = []
    
    if len(wt.get_graph_chars.get_unit_process_name_list(G)) > 1:
        for i in range(0, len(wt.get_graph_chars.get_unit_process_name_list(G))):
            x1.append([wt.get_graph_chars.get_unit_process_name_list(G)[i], G, cost_method])
    else:
        x1 = wt.get_graph_chars.get_unit_process_name_list(G)
        x1.append(G)
        x1.append(cost_method)
        x1 = [x1]
    
    print(x1)
    
    model.UnitProcesses3 = env.Set(initialize=x1)
    model.CalculateUPCosts = env.Constraint(model.UnitProcesses3,  rule=mc.calculate_up_total_costs)
       
    # OPTIMIZATION FOR LEV COST
    model.LevelizedCost = env.Var(model.RecoveredWaterNodes, bounds=(1e-20,None), initialize=1e-20)
    model.CalculateLevelizedCost = env.Constraint(model.RecoveredWaterNodes,  rule=mc.calculate_levelized_cost)
    
    ##### IF OPTIMIZING FOR PATHWAY #####
    
    y1 = sum(model.RecoveredCost[x] for x in model.RecoveredWaterNodes)
    y2 = sum(model.RecoveredFlow[x] for x in model.RecoveredWaterNodes)
    y3 = sum(model.LevelizedCost[x] for x in model.RecoveredWaterNodes)
    
    model.objective_function = env.Objective(expr= y1, sense=env.minimize)
        
    return model





def build_model1(G, cost_method = 'wt', optimize_path = False):
    
    model = env.ConcreteModel()
    
    # SETS
    model.LinkSet = env.Set(initialize=wt.get_graph_chars.get_link_list(G)) # all links in network
    model.UnitProcesses = env.Set(initialize=wt.get_graph_chars.get_unit_process_name_list(G)) # all unit processes
    model.SourceNodes = env.Set(initialize=wt.get_graph_chars.get_source_nodes(G)) # all source nodes
    model.AllNoneSourceEndNodes = env.Set(initialize=wt.get_graph_chars.get_all_none_source_end_nodes(G))
    model.RecoveredWaterNodes = env.Set(initialize=wt.get_graph_chars.get_recovered_water_nodes(G))
        
    # VARIABLES
    model.FlowInLinkSegments = env.Var(model.LinkSet, bounds=(1e-20,None), initialize=1e-20)
    model.TOCInLinkSegments = env.Var(model.LinkSet, bounds=(1e-20,None), initialize=1e-20)
    model.NitrateInLinkSegments = env.Var(model.LinkSet, bounds=(1e-20,None), initialize=1e-20)
    model.RecoveredFlow = env.Var(model.RecoveredWaterNodes, bounds=(1e-20,None), initialize=1e-20)
    model.RecoveredCost = env.Var(model.RecoveredWaterNodes, bounds=(1e-20,None), initialize=1e-20)
    model.TotalCostInLinkSegments = env.Var(model.LinkSet, bounds=(1e-20,None), initialize=1e-20)
    model.TDSInLinkSegments = env.Var(model.LinkSet, bounds=(1e-20,None), initialize=1e-20)

    # END NODE FLOW - > FOR OPTIMIZATION LIKELY NOT NEEDEDW
    x1 = []
    
    if len(wt.get_graph_chars.get_recovered_water_nodes(G)) > 1:
        for i in range(0, len(wt.get_graph_chars.get_recovered_water_nodes(G))):
            x1.append([wt.get_graph_chars.get_recovered_water_nodes(G)[i], G])
    else:
        x1 = wt.get_graph_chars.get_recovered_water_nodes(G)
        x1.append(G)
        x1 = [x1]
    
    model.RecoveredWaterNodes2 = env.Set(initialize=x1) # all recovered water
    model.CalculateRecoveredWater = env.Constraint(model.RecoveredWaterNodes2, rule=calculate_recovered_water)
    
    model.CalculateRecoveredCost = env.Constraint(model.RecoveredWaterNodes2, rule=calculate_total_train_cost)    
    
    ##############################

    water_variables = ['Flow' , 'TOC', 'Nitrate']#, 'TDS']
    x1 = []; x2 = []; x3 = [];
    for variable in water_variables:
        for i in range(0, len(wt.get_graph_chars.get_all_none_source_end_nodes(G))):
            x1.append([wt.get_graph_chars.get_all_none_source_end_nodes(G)[i], variable, G])
            
        for i in range(0, len(wt.get_graph_chars.get_source_nodes(G))):
            x2.append([wt.get_graph_chars.get_source_nodes(G)[i],  variable, G])            
            
        for i in range(0, len(wt.get_graph_chars.get_unit_process_name_list(G))):
            x3.append([wt.get_graph_chars.get_unit_process_name_list(G)[i], variable, G])     
    
    model.AllNoneSourceEndNodes2 = env.Set(initialize=x1)
    model.SourceNodes2 = env.Set(initialize=x2)
    model.UnitProcesses2 = env.Set(initialize=x3)

    # CONSTRAINTS FOR FLOW
    model.NodeMassBalanceConstraint = env.Constraint(model.AllNoneSourceEndNodes2, rule=node_mass_balance_constraint)
    model.CheckUnitInletFlows = env.Constraint(model.SourceNodes2, rule=source_flow_constraint)
    model.CalculateRecoveredFlows = env.Constraint(model.UnitProcesses2, rule=calculate_recovered_streams)

    # RECYCLE
    model.CalculateRecycleRecoveredFlows1 = env.Constraint(model.UnitProcesses2, rule=max_recycle_streams)  
    
    ## NEW CONSTRAINTS -> COST
    
    x1 = []
    
    if len(wt.get_graph_chars.get_unit_process_name_list(G)) > 1:
        for i in range(0, len(wt.get_graph_chars.get_unit_process_name_list(G))):
            x1.append([wt.get_graph_chars.get_unit_process_name_list(G)[i], G, cost_method])
    else:
        x1 = wt.get_graph_chars.get_unit_process_name_list(G)
        x1.append(G)
        x1.append(cost_method)
        x1 = [x1]
    
    print(x1)
    
    model.UnitProcesses3 = env.Set(initialize=x1)
    model.CalculateUPCosts = env.Constraint(model.UnitProcesses3,  rule=calculate_up_total_costs)
       
    # OPTIMIZATION FOR LEV COST
    model.LevelizedCost = env.Var(model.RecoveredWaterNodes, bounds=(1e-20,None), initialize=1e-20)
    model.CalculateLevelizedCost = env.Constraint(model.RecoveredWaterNodes,  rule=calculate_levelized_cost)
    
    ##### IF OPTIMIZING FOR PATHWAY #####
    
    y1 = sum(model.RecoveredCost[x] for x in model.RecoveredWaterNodes)
    y2 = sum(model.RecoveredFlow[x] for x in model.RecoveredWaterNodes)
    y3 = sum(model.LevelizedCost[x] for x in model.RecoveredWaterNodes)
    
    model.objective_function = env.Objective(expr= y1, sense=env.minimize)
        
    return model


def main():
    print("importing something")
    # need to define anything here?

if __name__ == "__main__":
    main()