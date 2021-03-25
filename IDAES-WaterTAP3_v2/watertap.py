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


def run_water_tap(m = None, solver_results = False, print_model_results = False, 
                  objective=False, max_attemps = 3, initialize_flow = 5, skip_small = True):
    
   
    # if flow is small it resets the flow to any inlet as 2 m3/s 
    if skip_small == False:
        for key in m.fs.flow_in_dict.keys():
            getattr(m.fs, key).flow_vol_in.fix(initialize_flow)
            small_flow = True
    
        # if flow is small it runs the model twice at most. then runs again with actual flows
        if small_flow is True: 
            print("Flow is relatively small (< 1 m3/s). Running model with larger dummy flows to initialize...\n")
            run_model(m = m, solver_results = False, print_model_results = False, 
                              objective=False, max_attemps = 1)

            print("Model finished running to initialize conditions. Now running with actual flow...\n")
            for key in m.fs.flow_in_dict.keys():
                getattr(m.fs, key).flow_vol_in.fix(m.fs.flow_in_dict[key])

            run_model(m = m, solver_results = solver_results, print_model_results = print_model_results, 
                              objective=objective, max_attemps = max_attemps)
        
        else:
            run_model(m = m, solver_results = solver_results, print_model_results = print_model_results, 
                              objective=objective, max_attemps = max_attemps)
    
    else:
        run_model(m = m, solver_results = solver_results, print_model_results = print_model_results, 
                      objective=objective, max_attemps = max_attemps)    
    
    if print_model_results: 
        print_results(m, print_model_results)
    
    #if return_results == True: return results



def watertap_setup(dynamic = False):
        
    # Create a Pyomo model
    m = ConcreteModel()

    # Add an IDAES FlowsheetBlock and set it to steady-state
    m.fs = FlowsheetBlock(default={"dynamic": dynamic})
    
    return m


def run_model(m = None, solver_results = False, print_model_results = False, 
                  objective=False, max_attemps = 0):
    import financials
    financials.get_system_costing(m.fs)
    
    # Transform Arc to construct linking equations
    TransformationFactory("network.expand_arcs").apply_to(m)
    seq = SequentialDecomposition()
    G = seq.create_graph(m)
    
    if objective == True:
        #m.fs.objective_function = env.Objective(expr=m.fs.reverse_osmosis.flow_vol_in[0], sense=env.maximize)
        m.fs.objective_function = env.Objective(expr=m.fs.costing.LCOW, sense=env.minimize)
        #m.fs.objective_function2 = env.Objective(expr=m.fs.costing.elec_frac_LCOW, sense=env.minimize)
    
    # Set up a solver in Pyomo and solve
    solver = SolverFactory('ipopt')
    #solver1.options = {'nlp_scaling_method': 'user-scaling'}
    #m.fs.initialize(optarg=solver1.options)
    
    import logging

    logging.getLogger('pyomo.core').setLevel(logging.ERROR)
    print("----------------------------------------------------------------------")
    print("\nDegrees of Freedom:", degrees_of_freedom(m))

    results = solver.solve(m, tee=solver_results)
    
    attempt_number = 1
    while ((results.solver.termination_condition == "infeasible") & (attempt_number <= max_attemps)):
        print("\nWaterTAP3 solver returned an infeasible solution...")
        print("Running again with updated initial conditions --- attempt %s" % (attempt_number))
        results = solver.solve(m, tee=solver_results)
        
        attempt_number = attempt_number + 1
    
    print("\nWaterTAP3 solution", results.solver.termination_condition, '\n')
    print("----------------------------------------------------------------------")

    if results.solver.termination_condition == "infeasible":
        print("\nWaterTAP3 solver returned an infeasible FINAL solution. Check option to run model with updated initial conditions.")
        print("----------------------------------------------------------------------")
    




    
def print_results(m, print_model_results):
    
    if print_model_results == "full":
        print("\n***UNIT PROCESS RESULTS (in $MM)***\n")
    # Display the inlets and outlets and cap cost of each unit
        for b_unit in m.fs.component_objects(Block, descend_into=True):
            unit = str(b_unit)[3:].replace('_', ' ').swapcase()
            if hasattr(b_unit, 'costing'):
                print(f'\n{unit}:\n')
                print("\n\n\ttotal cap investment:", round(value(b_unit.costing.total_cap_investment()), 5))
                print("\tcat and chem cost:", round(value(b_unit.costing.cat_and_chem_cost), 5))
                print("\telectricity cost:", round(value(b_unit.costing.electricity_cost), 5))
                print("\ttotal fixed op cost:", round(value(b_unit.costing.total_fixed_op_cost()), 5))
                print('\n')

            if hasattr(b_unit, 'inlet'):
                b_unit.inlet.display()
            if hasattr(b_unit, 'inlet1'):
                b_unit.inlet1.display()
            if hasattr(b_unit, 'outlet'):
                b_unit.outlet.display()
            if hasattr(b_unit, 'waste'):
                b_unit.waste.display()
        print("\n----------------------------------------------------------------------")

    
    if print_model_results == "summary":
        print("\n***UNIT PROCESS RESULTS (in $MM)***\n")
        for b_unit in m.fs.component_objects(Block, descend_into=True):
            if hasattr(b_unit, 'costing'):
                unit = str(b_unit)[3:].replace('_', ' ').swapcase()
                print(f'\n{unit}:\n')
                print("\ttotal cap investment:", round(value(b_unit.costing.total_cap_investment()), 5))
                print("\tcat and chem cost:", round(value(b_unit.costing.cat_and_chem_cost), 5))
                print("\telectricity cost:", round(value(b_unit.costing.electricity_cost), 5))
                print("\ttotal fixed op cost:", round(value(b_unit.costing.total_fixed_op_cost()), 5))
        print("\n----------------------------------------------------------------------")

            
    print("\n\n----------------------------------------------------------------------")
    print("------------------- System Level Metrics and Costs -------------------")
    print("Total Capital Investment ($MM)", round(value(m.fs.costing.capital_investment_total()), 3))
    print("Annual Fixed Operating Cost ($MM/yr)", round(value(m.fs.costing.fixed_op_cost_annual()), 3))
    print("Annual Catalysts and Chemicals Cost ($MM/yr)", round(value(m.fs.costing.cat_and_chem_cost_annual()), 3))
    print("Annual Electricity Costs ($MM/yr)", round(value(m.fs.costing.electricity_cost_annual()), 3))
    print("Annual Other Variable Costs ($MM/yr)", round(value(m.fs.costing.other_var_cost_annual()), 3))
    print("Annual Operating Costs ($MM/yr)", round(value(m.fs.costing.operating_cost_annual()), 3))
    print("Treated water (m3/s) --->", round(value(m.fs.costing.treated_water()), 3))
    print("Total water recovery (%) --->", round(value(100 * m.fs.costing.system_recovery()), 3))
    print("Electricity intensity (kwh/m3) ---> ", round(value(m.fs.costing.electricity_intensity()), 3))
    print("LCOW ($/m3) ---> ", round(value(m.fs.costing.LCOW()), 3))
    print("Electricity portion of LCOW (%) --->", round(value(100 * m.fs.costing.elec_frac_LCOW()), 3))
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