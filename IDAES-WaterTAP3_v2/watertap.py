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
                  objective=False, max_attemps = 3, initialize_flow = 5, skip_small = True, return_solution = False):
    
   
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
                  objective=False, max_attemps = 0, return_solution = False):
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
        print("\nWaterTAP3 solver returned an infeasible solution. Check option to run model with updated initial conditions.")
        print("----------------------------------------------------------------------")
    
    if return_solution is True: 
        return results.solver.termination_condition



    
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

    

def sensitivity_runs(m = None, save_results = False, return_results = False, 
                     scenario = None, case_study = None, skip_small_sens = True):
    # sensitivity analyses
    sens_df = pd.DataFrame()
    
    m_scenario = scenario
    
    lcow_list = []
    water_recovery_list = []
    scenario_value = []
    scenario_name = []
    elec_lcow = []
    elec_int = []

    lcow_list.append(value(m.fs.costing.LCOW))
    water_recovery_list.append(value(m.fs.costing.system_recovery))
    scenario_value.append("n/a")
    scenario_name.append(scenario)
    elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
    elec_int.append(value(m.fs.costing.electricity_intensity))

    runs_per_scenario = 20

    ############ onstream_factor 70-100% ############
    stash_value = m.fs.costing_param.plant_cap_utilization
    scenario = "Plant Capacity Utilization 70-100%"
    print("-------", scenario, "-------")
    ub = 1
    lb = 0.7
    step = (ub - lb) / runs_per_scenario
    for i in np.arange(lb, ub + step, step):
        m.fs.costing_param.plant_cap_utilization = i
        run_water_tap(m = m, objective=False, skip_small = True)
        print(scenario, "LCOW -->", m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))

    m.fs.costing_param.plant_cap_utilization = stash_value    
    ############################################################    
    
    print("-------", "RESET", "-------")
    run_water_tap(m = m, objective=False, skip_small = True)
    print("LCOW -->", m.fs.costing.LCOW())
    
    ############ WACC 5-10%############
    stash_value = m.fs.costing_param.wacc
    scenario = "Weighted Average Cost of Capital 5-10%"
    print("-------", scenario, "-------")
    ub = 0.1
    lb = 0.05
    step = (ub - lb) / runs_per_scenario
    for i in np.arange(lb, ub + step, step):
        m.fs.costing_param.wacc = i
        run_water_tap(m = m, objective=False, skip_small = True)
        print(scenario, "LCOW -->", m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))

    m.fs.costing_param.wacc = stash_value    
    ############################################################    
    print("-------", "RESET", "-------")
    run_water_tap(m = m, objective=False, skip_small = True)
    print("LCOW -->", m.fs.costing.LCOW())

    ############ salinity  +-30% ############
    stash_value = []
    for key in m.fs.flow_in_dict:   
        stash_value.append(value(getattr(m.fs, key).conc_mass_in[0, "tds"]))
    scenario = "Inlet TDS +-30%"
    print("-------", scenario, "-------")
    ub = 0.75
    lb = 1.25
    step = (ub - lb) / runs_per_scenario

    for i in np.arange(lb, ub + step, step):
        q=0
        for key in m.fs.flow_in_dict:
            getattr(m.fs, key).conc_mass_in[0, "tds"].fix(stash_value[q] * i)
            q = q + 1

        run_water_tap(m = m, objective=False, skip_small = skip_small_sens)
        print(scenario, "LCOW -->", m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))

    q=0
    for key in m.fs.flow_in_dict:    
        getattr(m.fs, key).conc_mass_in[0, "tds"].fix(stash_value[q])
        q = q + 1


    ############################################################
    print("-------", "RESET", "-------")
    run_water_tap(m = m, objective=False, skip_small = True)
    print("LCOW -->", m.fs.costing.LCOW())
    ############ inlet flow +-30% ############
    stash_value = []
    for key in m.fs.flow_in_dict:   
        stash_value.append(value(getattr(m.fs, key).flow_vol_in[0]))
    scenario = "Inlet Flow +-30%"
    print("-------", scenario, "-------")
    ub = 0.75
    lb = 1.25
    step = (ub - lb) / runs_per_scenario

    for i in np.arange(lb, ub + step, step):
        q=0
        for key in m.fs.flow_in_dict:
            getattr(m.fs, key).flow_vol_in[0].fix(stash_value[q] * i)
            q = q + 1

        run_water_tap(m = m, objective=False, skip_small = skip_small_sens)
        print(scenario, "LCOW -->", m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))

    q=0
    for key in m.fs.flow_in_dict:    
        getattr(m.fs, key).flow_vol_in[0].fix(stash_value[q])
        q = q + 1

    ############################################################
    print("-------", "RESET", "-------")
    run_water_tap(m = m, objective=False, skip_small = True)
    print("LCOW -->", m.fs.costing.LCOW())
    ############ lifetime years ############

    stash_value = value(m.fs.costing_param.plant_lifetime_yrs)
    scenario = "Plant Lifetime 15-45 yrs"
    print("-------", scenario, "-------")
    ub = 45
    lb = 15
    step = (ub - lb) / runs_per_scenario
    for i in np.arange(lb, ub + step, step):
        m.fs.costing_param.plant_lifetime_yrs = i 
        run_water_tap(m = m, objective=False, skip_small = True)
        print(scenario, "LCOW -->", m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))

    m.fs.costing_param.plant_lifetime_yrs = stash_value
    ############################################################
    print("-------", "RESET", "-------")
    run_water_tap(m = m, objective=False, skip_small = True)
    print("LCOW -->", m.fs.costing.LCOW())
    ############ elec cost +-30% ############

    stash_value = value(m.fs.costing_param.electricity_price)
    scenario = "electricity price +- 30%"
    print("-------", scenario, "-------")
    ub = stash_value * 1.3
    lb = stash_value * 0.7
    step = (ub - lb) / runs_per_scenario
    for i in np.arange(lb, ub + step, step):
        m.fs.costing_param.electricity_price = i 
        run_water_tap(m = m, objective=False, skip_small = True)
        print(scenario, "LCOW -->", m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))

    m.fs.costing_param.electricity_price = stash_value
    ############################################################
    print("-------", "RESET", "-------")
    run_water_tap(m = m, objective=False, skip_small = True)
    print("LCOW -->", m.fs.costing.LCOW())
    ############ RO scenarios --> pressure % change, membrane area, replacement rate% ############

    for key in m.fs.pfd_dict.keys():
        if m.fs.pfd_dict[key]["Unit"] == "reverse_osmosis":
            area = value(getattr(m.fs, key).membrane_area[0])

            scenario_dict = {"membrane_area" : [-area*0.1, area*0.1], 
                             "pressure": [0.9, 1.1], 
                             "factor_membrane_replacement": [-0.1, 0.3]}

            for scenario in scenario_dict.keys():
                
                print("-------", "RESET", "-------")
                run_water_tap(m = m, objective=False, skip_small = True)
                print("LCOW -->", m.fs.costing.LCOW())
                
                print("-------", scenario, "-------")
                if scenario == "pressure":
                    stash_value = value(getattr(getattr(getattr(m.fs, key), "feed"), scenario)[0])
                    ub = stash_value * scenario_dict[scenario][1]
                    lb = stash_value * scenario_dict[scenario][0]
                else:
                    stash_value = value(getattr(getattr(m.fs, key), scenario)[0])
                    ub = stash_value + scenario_dict[scenario][1]
                    lb = stash_value + scenario_dict[scenario][0]

                step = (ub - lb) / runs_per_scenario

                for i in np.arange(lb, ub + step, step):
                    if scenario == "pressure":
                        getattr(getattr(getattr(m.fs, key), "feed"), scenario).fix(i)
                    else:
                        getattr(getattr(m.fs, key), scenario).fix(i)

                    run_water_tap(m = m, objective=False, skip_small = skip_small_sens)
                    print(scenario, "LCOW -->", m.fs.costing.LCOW())

                    lcow_list.append(value(m.fs.costing.LCOW))
                    water_recovery_list.append(value(m.fs.costing.system_recovery))
                    scenario_value.append(i)
                    scenario_name.append(key + "_" + scenario)
                    elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
                    elec_int.append(value(m.fs.costing.electricity_intensity))

                if scenario == "pressure":
                    getattr(getattr(getattr(m.fs, key), "feed"), scenario).fix(stash_value)
                else:
                    getattr(getattr(m.fs, key), scenario).fix(stash_value)

    ############################################################

    # final run to get baseline numbers again
    run_water_tap(m = m, objective=False, skip_small = skip_small_sens)

    sens_df["lcow"] = lcow_list
    sens_df["water_recovery"] =  water_recovery_list
    sens_df["elec_lcow"] =  elec_lcow
    sens_df["elec_int"] =  elec_int
    sens_df["scenario_value"] = scenario_value
    sens_df["scenario_name"] = scenario_name
    sens_df["lcow_difference"] =  sens_df.lcow - value(m.fs.costing.LCOW)
    sens_df["water_recovery_difference"] = (sens_df.water_recovery - value(m.fs.costing.system_recovery))
    sens_df["elec_lcow_difference"] = (sens_df.elec_lcow - value(m.fs.costing.elec_frac_LCOW))

    sens_df.elec_lcow = sens_df.elec_lcow * 100
    sens_df.water_recovery = sens_df.water_recovery * 100
    
    if save_results is True:
        sens_df.to_csv("results/case_studies/%s_%s_sensitivity.csv" % (case_study, m_scenario))
    if return_results is True:
        return sens_df
    
    

        
def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()