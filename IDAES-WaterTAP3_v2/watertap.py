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
import optimize_setup

warnings.filterwarnings('ignore')

from pyomo.environ import ConcreteModel, SolverFactory, TransformationFactory
from pyomo.network import SequentialDecomposition
from idaes.core import FlowsheetBlock

from idaes.core.util.model_statistics import degrees_of_freedom
from pyomo.util.check_units import assert_units_consistent
import pyomo.util.infeasible as infeas
import idaes.core.util.scaling as iscale
import pyomo.environ as env

def watertap_setup(dynamic = False):
        
    # Create a Pyomo model
    m = ConcreteModel()

    # Add an IDAES FlowsheetBlock and set it to steady-state
    m.fs = FlowsheetBlock(default={"dynamic": dynamic})
    
    return m


def run_water_tap(m = None, solver_results = False, print_model_results = False, 
                  objective=False, return_results = True, max_attemps = 0):
    import financials
    financials.get_system_costing(m.fs)
    
    # Transform Arc to construct linking equations
    TransformationFactory("network.expand_arcs").apply_to(m)
    seq = SequentialDecomposition()
    G = seq.create_graph(m)
    
    if objective == True:
        #m.fs.objective_function = env.Objective(expr=m.fs.reverse_osmosis.flow_vol_in[0], sense=env.maximize)
        m.fs.objective_function = env.Objective(expr=m.fs.costing.LCOW, sense=env.minimize)
        #m.fs.objective_function2 = env.Objective(expr=m.fs.municipal_drinking.flow_vol_in[0], sense=env.minimize)
    
    # Set up a solver in Pyomo and solve
    solver = SolverFactory('ipopt')
    #solver1.options = {'nlp_scaling_method': 'user-scaling'}
    #m.fs.initialize(optarg=solver1.options)
    
    import logging

    logging.getLogger('pyomo.core').setLevel(logging.ERROR)
    
    print("degrees_of_freedom:", degrees_of_freedom(m))
    
    #solver.options = {'nlp_scaling_method': 'user-scaling'}
    #m.fs.initialize(optarg=solver.options)
    
    #solver.solve(m, tee=solver_results)
    
    results = solver.solve(m, tee=solver_results)
    
    attempt_number = 1
    while ((results.solver.termination_condition == "infeasible") & (attempt_number <= max_attemps)):
        print("WaterTAP3 solver returned an infeasible solution")
        print("Running again with updated initial conditions --- attempt %s" % (attempt_number))
        results = solver.solve(m, tee=solver_results)
        
        attempt_number = attempt_number + 1
    
    print("WaterTAP3 solution", results.solver.termination_condition)

    if results.solver.termination_condition == "infeasible":
        print("WaterTAP3 solver returned an infeasible FINAL solution. Check option to run model with updated initial conditions")
    
    if print_model_results == True:
    
        # Display the inlets and outlets and cap cost of each unit
        for b_unit in m.fs.component_objects(Block, descend_into=True):

            
            if hasattr(b_unit, 'inlet'):
                print("----------------------------------------------------------------------")
                print(b_unit)
                b_unit.inlet.display()
            if hasattr(b_unit, 'inlet1'):
                print("----------------------------------------------------------------------")
                print(b_unit)
                b_unit.inlet1.display()
            if hasattr(b_unit, 'outlet'): b_unit.outlet.display()
            if hasattr(b_unit, 'waste'): b_unit.waste.display()
            if hasattr(b_unit, 'costing'):

                print("total_cap_investment:", b_unit.costing.total_cap_investment())
                print("----------------------------------------------------------------------")
       
    if return_results == True: return results
    
            
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