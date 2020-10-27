from pylab import *

import shutil
import sys
import os.path
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
from scipy.optimize import fsolve
from scipy.optimize import minimize
import itertools
import pyomo.environ as env
import ast
from pyomo.environ import *
import networkx as nx
from networkx.drawing.nx_agraph import write_dot, graphviz_layout

### WATER TAP MODULES ###
from src import importfile
from src import treatment_train_design
from src import display
from src import get_graph_chars
from src import filter_processes
from src import post_processing
from src import get_model_chars
from src import save_train_module
from src import module_import
from src import model_constraints #as mc
from src import load_train_module

### units that pre-exist ###
unit_process_library_list = [
    "chlorination_twb",
    "media_filtration_twb",
    "microfiltration_twb",
    "ultrafiltration_twb",
    "nanofiltration_twb",
    "coag_and_floc"
    "ro_twb",
    "uv_twb",
    "ro_bor",
    "uvozone_twb",
    "mbr",
    "water_pumping_station"
]


fw_filename = "data/case_study_water_sources_and_uses.csv"
water_source_use_library = importfile.feedwater(
    input_file=fw_filename,
    reference=None,
    case_study=None,
    water_type=None,
    source_or_use=None,
)

unit = "m3d" # this is not used yet

def save_train(G, path):

    edge_df = save_train_module.get_edge_df(G)
    node_df = save_train_module.get_node_df(G)

    df = pd.concat([edge_df, node_df], axis=0)

    df.to_csv(path, index=False)

    return


def load_train(path):

    df = pd.read_csv(path)
    G = nx.DiGraph(directed=True)
    G = load_train_module.load_edges(G, df)
    G = load_train_module.load_nodes(G, df)

    return G


def build_model(G, cost_method="wt", optimize_path=False):

    model = env.ConcreteModel()

    # SETS
    model.LinkSet = env.Set(
        initialize=get_graph_chars.get_link_list(G)
    )  # all links in network
    model.UnitProcesses = env.Set(
        initialize=get_graph_chars.get_unit_process_name_list(G)
    )  # all unit processes
    model.SourceNodes = env.Set(
        initialize=get_graph_chars.get_source_nodes(G)
    )  # all source nodes
    model.AllNoneSourceEndNodes = env.Set(
        initialize=get_graph_chars.get_all_none_source_end_nodes(G)
    )
    model.RecoveredWaterNodes = env.Set(
        initialize=get_graph_chars.get_recovered_water_nodes(G)
    )

    # VARIABLES
    model.FlowInLinkSegments = env.Var(
        model.LinkSet, bounds=(1e-20, None), initialize=1e-20
    )
    model.TOCInLinkSegments = env.Var(
        model.LinkSet, bounds=(1e-20, None), initialize=1e-20
    )
    model.NitrateInLinkSegments = env.Var(
        model.LinkSet, bounds=(1e-20, None), initialize=1e-20
    )
    model.RecoveredFlow = env.Var(
        model.RecoveredWaterNodes, bounds=(1e-20, None), initialize=1e-20
    )
    model.RecoveredCost = env.Var(
        model.RecoveredWaterNodes, bounds=(1e-20, None), initialize=1e-20
    )
    model.TotalCostInLinkSegments = env.Var(
        model.LinkSet, bounds=(1e-20, None), initialize=1e-20
    )
    model.TDSInLinkSegments = env.Var(
        model.LinkSet, bounds=(1e-20, None), initialize=1e-20
    )

    # BINARY TEST
    model.y = env.Var(model.LinkSet, within=Binary)

    # END NODE FLOW - > FOR OPTIMIZATION LIKELY NOT NEEDEDW
    x1 = []

    if len(get_graph_chars.get_recovered_water_nodes(G)) > 1:
        for i in range(0, len(get_graph_chars.get_recovered_water_nodes(G))):
            x1.append([get_graph_chars.get_recovered_water_nodes(G)[i], G])
    else:
        x1 = get_graph_chars.get_recovered_water_nodes(G)
        x1.append(G)
        x1 = [x1]

    model.RecoveredWaterNodes2 = env.Set(initialize=x1)  # all recovered water
    model.CalculateRecoveredWater = env.Constraint(
        model.RecoveredWaterNodes2, rule=model_constraints.calculate_recovered_water
    )

    model.CalculateRecoveredCost = env.Constraint(
        model.RecoveredWaterNodes2, rule=model_constraints.calculate_total_train_cost
    )

    ##############################

    water_variables = ["Flow", "TOC", "Nitrate"]  # , 'TDS']
    x1 = []
    x2 = []
    x3 = []
    for variable in water_variables:
        for i in range(0, len(get_graph_chars.get_all_none_source_end_nodes(G))):
            x1.append(
                [get_graph_chars.get_all_none_source_end_nodes(G)[i], variable, G]
            )

        for i in range(0, len(get_graph_chars.get_source_nodes(G))):
            x2.append([get_graph_chars.get_source_nodes(G)[i], variable, G])

        for i in range(0, len(get_graph_chars.get_unit_process_name_list(G))):
            x3.append(
                [get_graph_chars.get_unit_process_name_list(G)[i], variable, G]
            )

    model.AllNoneSourceEndNodes2 = env.Set(initialize=x1)
    model.SourceNodes2 = env.Set(initialize=x2)
    model.UnitProcesses2 = env.Set(initialize=x3)

    # CONSTRAINTS FOR FLOW
    model.NodeMassBalanceConstraint = env.Constraint(
        model.AllNoneSourceEndNodes2, rule=model_constraints.node_mass_balance_constraint
    )
    model.CheckUnitInletFlows = env.Constraint(
        model.SourceNodes2, rule=model_constraints.source_flow_constraint
    )
    model.CalculateRecoveredFlows = env.Constraint(
        model.UnitProcesses2, rule=model_constraints.calculate_recovered_streams
    )

    # RECYCLE
    model.CalculateRecycleRecoveredFlows1 = env.Constraint(
        model.UnitProcesses2, rule=model_constraints.max_recycle_streams
    )

    ## NEW CONSTRAINTS -> COST

    x1 = []

    if len(get_graph_chars.get_unit_process_name_list(G)) > 1:
        for i in range(0, len(get_graph_chars.get_unit_process_name_list(G))):
            x1.append(
                [get_graph_chars.get_unit_process_name_list(G)[i], G, cost_method]
            )
    else:
        x1 = get_graph_chars.get_unit_process_name_list(G)
        x1.append(G)
        x1.append(cost_method)
        x1 = [x1]

    model.UnitProcesses3 = env.Set(initialize=x1)
    model.CalculateUPCosts = env.Constraint(
        model.UnitProcesses3, rule=model_constraints.calculate_up_total_costs
    )

    # OPTIMIZATION FOR LEV COST
    model.LevelizedCost = env.Var(
        model.RecoveredWaterNodes, bounds=(1e-20, None), initialize=1e-20
    )
    model.CalculateLevelizedCost = env.Constraint(
        model.RecoveredWaterNodes, rule=model_constraints.calculate_levelized_cost
    )

    ##### IF OPTIMIZING FOR PATHWAY #####

    y1 = sum(model.RecoveredCost[x] for x in model.RecoveredWaterNodes)
    y2 = sum(model.RecoveredFlow[x] for x in model.RecoveredWaterNodes)
    y3 = sum(model.LevelizedCost[x] for x in model.RecoveredWaterNodes)

    model.objective_function = env.Objective(expr=y1, sense=env.minimize)

    return model


def run_model(G=None, cost_method="wt", optimize_path=False, model=None):

    if model is None:
        model = build_model(G, cost_method="wt", optimize_path=False)
        solver = env.SolverFactory("ipopt")
        solved = solver.solve(model)

    else:
        solver = env.SolverFactory("ipopt")
        solved = solver.solve(model)

    return solved


def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()
