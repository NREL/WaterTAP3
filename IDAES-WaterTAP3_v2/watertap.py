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
from pyomo.environ import ConcreteModel, SolverFactory, TransformationFactory
from pyomo.network import Arc, SequentialDecomposition
import pyomo.environ as env
from idaes.core import FlowsheetBlock



# Import properties and units from "WaterTAP Library"
from water_props import WaterParameterBlock
#from model_example import UnitProcess
from source_example import Source
from split_test2 import Separator1

from mixer_example import Mixer1

### WATER TAP MODULES ###
import financials
import display
import watertap as wt
import case_study_trains
import importfile
import module_import
import design
import case_study_trains
from post_processing import *
import app3 

import warnings
warnings.filterwarnings('ignore')

from pyomo.environ import ConcreteModel, SolverFactory, TerminationCondition, \
    value, Var, Constraint, Expression, Objective, TransformationFactory, units as pyunits
from pyomo.network import Arc, SequentialDecomposition
from idaes.core import FlowsheetBlock
from idaes.generic_models.unit_models import Mixer, Pump

from idaes.generic_models.unit_models import Separator as Splitter

from idaes.core.util.model_statistics import degrees_of_freedom
from pyomo.util.check_units import assert_units_consistent
import pyomo.util.infeasible as infeas
import idaes.core.util.scaling as iscale
#from src import treatment_train_design
#from src import display
#from src import get_graph_chars
#from src import filter_processes
#from src import post_processing
#from src import get_model_chars
#from src import save_train_module
#from src import module_import
#from src import model_constraints #as mc
#from src import load_train_module

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
    "water_pumping_station",
    "ro_deep",
    "media_filtration",
    "coag_and_floc",
    "lime_softening",
    "ro_deep",
    "treated_storage_24_hr",
    "sedimentation",
    "water_pumping_station",
    "sulfuric_acid_addition",
    "sodium_bisulfite_addition",
    "co2_addition",
    "ammonia_addition",
    "municipal_drinking",
    "sw_onshore_intake",
    "holding_tank",
    "tri_media_filtration",
    "cartridge_filtration",
    "backwash_solids_handling",
    "surface_discharge",
    "landfill",
    "coagulant_addition",
    "fecl3_addition", 
    "caustic_soda_addition", 
    "static_mix",
    "ro_deep_scnd_pass", 
    "anti_scalant_addition",
    "ro_deep_scnd_pass",
    "uv_aop"]



fw_filename = "data/case_study_water_sources_and_uses.csv"
water_source_use_library = importfile.feedwater(
    input_file=fw_filename,
    reference=None,
    case_study=None,
    water_type=None,
    source_or_use=None,
)



def watertap_setup(dynamic = False):
    
    # get constituents for treatment train needed for water property package
    
    # Create a Pyomo model
    m = ConcreteModel()

    # Add an IDAES FlowsheetBlock and set it to steady-state
    m.fs = FlowsheetBlock(default={"dynamic": dynamic})

    # Add water property package (this can be updated to account for a more extensive list of properties)
    #m.fs.water = WaterParameterBlock() -> THIS IS MOVED TO CASE STUDIES BECAUSE WE CAN'T ADD THIS WITHOUT KNOWING WHICH STUDY

    return m


def run_water_tap(m = None, solver_results = False, print_model_results = False):
    import financials
    financials.get_system_costing(m.fs)
    
    # Transform Arc to construct linking equations
    TransformationFactory("network.expand_arcs").apply_to(m)
    seq = SequentialDecomposition()
    G = seq.create_graph(m)
    
    # Set up a solver in Pyomo and solve

    solver1 = SolverFactory('ipopt')
    
    import logging

    logging.getLogger('pyomo.core').setLevel(logging.ERROR)
    
    print("degrees_of_freedom:", degrees_of_freedom(m))
    
    solver1.solve(m, tee=solver_results)
    
    if print_model_results == True:
    
        #print("degrees_of_freedom:", degrees_of_freedom(m))

        # Display the inlets and outlets of each unit
        for node in G.nodes():
            print("----------------------------------------------------------------------")
            print(node)

            if "split" in (str(node).replace('fs.', '')): 
                getattr(m.fs, str(node).replace('fs.', '')).inlet.display()
                getattr(m.fs, str(node).replace('fs.', '')).outlet1.display()
                getattr(m.fs, str(node).replace('fs.', '')).outlet2.display()
            elif "use" in (str(node).replace('fs.', '')): 
                getattr(m.fs, str(node).replace('fs.', '')).inlet.display()
                getattr(m.fs, str(node).replace('fs.', '')).outlet.display()
            elif "mixer" in (str(node).replace('fs.', '')): 
                getattr(m.fs, str(node).replace('fs.', '')).inlet1.display()
                getattr(m.fs, str(node).replace('fs.', '')).inlet2.display()
                getattr(m.fs, str(node).replace('fs.', '')).outlet.display()
            else:
                getattr(m.fs, str(node).replace('fs.', '')).inlet.display()
                getattr(m.fs, str(node).replace('fs.', '')).outlet.display()
                getattr(m.fs, str(node).replace('fs.', '')).waste.display()


            print("Show some costing values")
            print("---------------------")

            if "Seawater" in (str(node).replace('fs.', '')): 
                print("should skip:", (str(node).replace('fs.', '')))
                continue
            elif "use" in (str(node).replace('fs.', '')): 
                print("should skip:", (str(node).replace('fs.', '')))
                continue
            elif "split" in (str(node).replace('fs.', '')): 
                print("should skip:", (str(node).replace('fs.', '')))
                continue  
            elif "mixer" in (str(node).replace('fs.', '')): 
                print("should skip:", (str(node).replace('fs.', '')))
                continue
            else:
                print("should have a cost", (str(node).replace('fs.', '')))
                if getattr(m.fs, str(node).replace('fs.', '')).costing.total_up_cost() is not None:
                    print("total_up_cost:" , 
                          getattr(m.fs, str(node).replace('fs.', '')).costing.total_up_cost())

                else:
                    getattr(m.fs, str(node).replace('fs.', '')).costing.total_up_cost.display()

            print("----------------------------------------------------------------------")

            
def run_model_comparison(scenarioA, scenarioB, flow = 4.5833):
    import pandas as pd
    final_df = pd.DataFrame()
    for scenario in [scenarioA, scenarioB]:
    
        wt.case_study_trains.case_study = "Carlsbad"
        wt.case_study_trains.reference = "NAWI"
        wt.case_study_trains.water_type = "Seawater"
        wt.case_study_trains.scenario = scenario

        # eventually we may want to be able to choose a dynamic model or different model set ups.
        m = wt.watertap_setup(dynamic = False)

        # load the treatment train, source water information, and flow to the model.
        m = wt.case_study_trains.get_case_study(flow = flow, m = m)

        #run model
        wt.run_water_tap(m = m, solver_results = False, print_model_results = False)

        df = wt.get_results_table(m = m)
        
        final_df = pd.concat([final_df ,df])
    
    final_df.to_csv("results/CarlsbadCompare.csv")
    
    return final_df            

        
def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()