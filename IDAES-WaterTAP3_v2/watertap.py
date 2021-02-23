# Import properties and units from "WaterTAP Library"
# from model_example import UnitProcess

import warnings

import case_study_trains
### WATER TAP MODULES ###
import financials
import display
import watertap as wt
import case_study_trains
import importfile
import module_import
import design
import case_study_trains
import watertap as wt
from post_processing import *
import app3

warnings.filterwarnings('ignore')

from pyomo.environ import ConcreteModel, SolverFactory, TransformationFactory
from pyomo.network import SequentialDecomposition
from idaes.core import FlowsheetBlock

from idaes.core.util.model_statistics import degrees_of_freedom


def watertap_setup(dynamic = False):
        
    # Create a Pyomo model
    m = ConcreteModel()

    # Add an IDAES FlowsheetBlock and set it to steady-state
    m.fs = FlowsheetBlock(default={"dynamic": dynamic})
    
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
    
        # Display the inlets and outlets and cap cost of each unit
        for b_unit in m.fs.component_objects(Block, descend_into=True):

            
            if hasattr(b_unit, 'inlet'):
                print("----------------------------------------------------------------------")
                print(b_unit)
                b_unit.inlet.display()
            if hasattr(b_unit, 'outlet'): b_unit.outlet.display()
            if hasattr(b_unit, 'waste'): b_unit.waste.display()
            if hasattr(b_unit, 'costing'):

                print("total_cap_investment:", b_unit.costing.total_cap_investment())
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