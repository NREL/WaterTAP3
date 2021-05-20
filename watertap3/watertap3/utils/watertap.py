import ast
import logging
import warnings

import pandas as pd
import numpy as np
from idaes.core import FlowsheetBlock
from idaes.core.util.model_statistics import degrees_of_freedom
from pyomo.environ import Block, ConcreteModel, Constraint, Objective, SolverFactory, TransformationFactory, value
from pyomo.network import SequentialDecomposition

from . import financials
from .case_study_trains import *
from .post_processing import get_results_table

warnings.filterwarnings('ignore')

__all__ = ['run_water_tap',
           'watertap_setup',
           'run_model',
           'run_water_tap',
           'run_water_tap_ro',
           'run_sensitivity',
           'print_ro_results',
           'print_results',
           'set_bounds',
           'unset_bounds']


def run_water_tap(m=None, solver_results=False, print_model_results=False,
                  objective=False, max_attempts=3, initialize_flow=5, skip_small=True,
                  return_solution=False,
                  sensitivity_flow=None):
    # if flow is small it resets the flow to any inlet as 2 m3/s
    if skip_small == False:
        for key in m.fs.flow_in_dict.keys():
            getattr(m.fs, key).flow_vol_in.fix(initialize_flow)
            small_flow = True

        # if flow is small it runs the model twice at most. then runs again with actual flows
        if small_flow:
            print('Flow is relatively small (< 1 m3/s). Running model with larger dummy flows to initialize...\n')
            run_model(m=m, solver_results=False, print_model_results=False,
                      objective=False, max_attempts=1)

            print('Model finished running to initialize conditions. Now running with actual flow...\n')

            for key in m.fs.flow_in_dict.keys():
                if sensitivity_flow is None:
                    getattr(m.fs, key).flow_vol_in.fix(m.fs.flow_in_dict[key])
                else:
                    getattr(m.fs, key).flow_vol_in.fix(sensitivity_flow[key])

            run_model(m=m, solver_results=solver_results, print_model_results=print_model_results,
                      objective=objective, max_attempts=max_attempts)

        else:
            run_model(m=m, solver_results=solver_results, print_model_results=print_model_results,
                      objective=objective, max_attempts=max_attempts)

    else:
        run_model(m=m, solver_results=solver_results, print_model_results=print_model_results,
                  objective=objective, max_attempts=max_attempts)

    if print_model_results:
        print_results(m, print_model_results)


def watertap_setup(dynamic=False, case_study=None, reference=None, scenario=None, source_reference=None, source_case_study=None, source_scenario=None):
    m = ConcreteModel()

    m.fs = FlowsheetBlock(default={'dynamic': dynamic})

    m.fs.train = {'case_study': case_study, 'reference': reference, 'scenario': scenario}

    if source_reference is None:
        source_reference = reference
    if source_case_study is None:
        source_case_study = case_study
    if source_scenario is None:
        source_scenario = scenario

    df = pd.read_excel('data/treatment_train_setup.xlsx', sheet_name='units')

    df = filter_df(df, m)
    water_type_list = []

    for i in list(df[df.Type == 'intake'].index):
        for water_type in ast.literal_eval(df[df.Type == 'intake'].loc[i]['Parameter'])['water_type']:
            water_type_list.append(water_type)

    if len(water_type_list) == 1:
        water_type_list = water_type_list[0]

    m.fs.source_water = {
            'case_study': source_case_study, 'reference': source_reference,
            'scenario': source_scenario, 'water_type': water_type_list
            }

    return m


def run_model(m=None, solver_results=False, print_model_results=False, objective=False, max_attempts=0, return_solution=False):
    financials.get_system_costing(m.fs)

    TransformationFactory('network.expand_arcs').apply_to(m)
    seq = SequentialDecomposition()
    G = seq.create_graph(m)

    if objective == True:
        m.fs.objective_function = Objective(expr=m.fs.costing.LCOW)

    solver = SolverFactory('ipopt')
    logging.getLogger('pyomo.core').setLevel(logging.ERROR)
    print('----------------------------------------------------------------------')
    print('\nDegrees of Freedom:', degrees_of_freedom(m))

    results = solver.solve(m, tee=solver_results)

    attempt_number = 1
    while ((results.solver.termination_condition == 'infeasible') & (attempt_number <= max_attempts)):
        print(f'\nAttempt {attempt_number}')
        print('\nWaterTAP3 solver returned an infeasible solution...\n')
        print(f'Running again with updated initial conditions --- attempt {attempt_number}\n')
        results = solver.solve(m, tee=solver_results)

        attempt_number += 1

    print('\nWaterTAP3 solution', results.solver.termination_condition, '\n')
    print('----------------------------------------------------------------------')

    if results.solver.termination_condition == 'infeasible':
        print('\nWaterTAP3 solver returned an infeasible solution. Check option to run model with updated initial conditions.\n\n')
        print('----------------------------------------------------------------------')

    if return_solution is True:
        return results.solver.termination_condition


def print_results(m, print_model_results):
    if print_model_results == 'full':
        print('\n***UNIT PROCESS RESULTS (in $MM)***\n')
        # Display the inlets and outlets and cap cost of each unit
        for b_unit in m.fs.component_objects(Block, descend_into=True):
            unit = str(b_unit)[3:].replace('_', ' ').swapcase()
            if hasattr(b_unit, 'costing'):
                print(f'\n{unit}:\n')
                print('\n\n\ttotal cap investment:', round(value(b_unit.costing.total_cap_investment()), 5))
                print('\tcat and chem cost:', round(value(b_unit.costing.cat_and_chem_cost), 5))
                print('\telectricity cost:', round(value(b_unit.costing.electricity_cost), 5))
                print('\ttotal fixed op cost:', round(value(b_unit.costing.total_fixed_op_cost), 5))
                print('\n')

            if hasattr(b_unit, 'inlet'):
                b_unit.inlet.display()
            if hasattr(b_unit, 'inlet1'):
                b_unit.inlet1.display()
            if hasattr(b_unit, 'outlet'):
                b_unit.outlet.display()
            if hasattr(b_unit, 'waste'):
                b_unit.waste.display()
        print('\n----------------------------------------------------------------------\n')

    if print_model_results == 'summary':
        print('\n***UNIT PROCESS RESULTS (in $MM)***\n')
        for b_unit in m.fs.component_objects(Block, descend_into=True):
            if hasattr(b_unit, 'costing'):
                unit = str(b_unit)[3:].replace('_', ' ').swapcase()
                print(f'\n{unit}:\n')
                print('\ttotal cap investment:', round(value(b_unit.costing.total_cap_investment()), 5))
                print('\tcat and chem cost:', round(value(b_unit.costing.cat_and_chem_cost), 5))
                print('\telectricity cost:', round(value(b_unit.costing.electricity_cost), 5))
                print('\ttotal fixed op cost:', round(value(b_unit.costing.total_fixed_op_cost), 5))
        print('\n----------------------------------------------------------------------')

    print('\n\n----------------------------------------------------------------------\n\n')
    print('------------------- System Level Metrics and Costs -------------------')
    print('Total Capital Investment ($MM)',
          round(value(m.fs.costing.capital_investment_total()), 3))
    print('Annual Fixed Operating Cost ($MM/yr)',
          round(value(m.fs.costing.fixed_op_cost_annual()), 3))
    print('Annual Catalysts and Chemicals Cost ($MM/yr)',
          round(value(m.fs.costing.cat_and_chem_cost_annual()), 3))
    print('Annual Electricity Costs ($MM/yr)',
          round(value(m.fs.costing.electricity_cost_annual()), 3))
    print('Annual Other Variable Costs ($MM/yr)',
          round(value(m.fs.costing.other_var_cost_annual()), 3))
    print('Annual Operating Costs ($MM/yr)',
          round(value(m.fs.costing.operating_cost_annual()), 3))
    print('Treated water (m3/s) --->',
          round(value(m.fs.costing.treated_water()), 3))
    print('Total water recovery (%) --->',
          round(value(100 * m.fs.costing.system_recovery()), 3))
    print('Electricity intensity (kwh/m3) ---> ',
          round(value(m.fs.costing.electricity_intensity()), 3))
    print('LCOW ($/m3) ---> ',
          round(value(m.fs.costing.LCOW()), 3))
    print('Electricity portion of LCOW (%) --->',
          round(value(100 * m.fs.costing.elec_frac_LCOW()), 3))
    print('----------------------------------------------------------------------')


def run_sensitivity(m=None, save_results=False, return_results=False,
                     scenario=None, case_study=None, skip_small_sens=True):
    ro_list = ['reverse_osmosis', 'ro_first_pass', 'ro_a1', 'ro_b1',
               'ro_active', 'ro_restore']

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
    scenario_value.append('n/a')
    scenario_name.append(scenario)
    elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
    elec_int.append(value(m.fs.costing.electricity_intensity))

    runs_per_scenario = 20

    ############ onstream_factor 70-100% ############
    stash_value = m.fs.costing_param.plant_cap_utilization
    scenario = 'Plant Capacity Utilization 70-100%'
    print('-------', scenario, '-------')
    ub = 1
    lb = 0.7
    step = (ub - lb) / runs_per_scenario
    for i in np.arange(lb, ub + step, step):
        m.fs.costing_param.plant_cap_utilization = i
        run_water_tap(m=m, objective=False, skip_small=True)
        print(scenario, i, 'LCOW -->', m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))

    m.fs.costing_param.plant_cap_utilization = stash_value
    ############################################################    

    print('\n-------', 'RESET', '-------\n')
    run_water_tap(m=m, objective=False, skip_small=True)
    print('LCOW -->', m.fs.costing.LCOW())

    ############ WACC 5-10%############
    stash_value = m.fs.costing_param.wacc
    scenario = 'Weighted Average Cost of Capital 5-10%'
    print('-------', scenario, '-------')
    ub = 0.1
    lb = 0.05
    step = (ub - lb) / runs_per_scenario
    for i in np.arange(lb, ub + step, step):
        m.fs.costing_param.wacc = i
        run_water_tap(m=m, objective=False, skip_small=True)
        print(scenario, i, 'LCOW -->', m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))

    m.fs.costing_param.wacc = stash_value
    ############################################################    

    tds_in = False

    for key in m.fs.flow_in_dict:
        if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
            tds_in = True

    if tds_in is True:
        print('\n-------', 'RESET', '-------\n')
        run_water_tap(m=m, objective=False, skip_small=True)
        print('LCOW -->', m.fs.costing.LCOW())

        ############ salinity  +-30% ############
        stash_value = []
        for key in m.fs.flow_in_dict:
            if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
                stash_value.append(value(getattr(m.fs, key).conc_mass_in[0, 'tds']))
        print(stash_value)
        scenario = 'Inlet TDS +-25%'
        print('-------', scenario, '-------')
        ub = 1.25
        lb = 0.75

        if m_scenario in ['edr_ph_ro', 'ro_and_mf']:
            print('redoing upper and lower bounds')
            ub = 80
            lb = 60

        step = (ub - lb) / runs_per_scenario

        for i in np.arange(lb, ub + step, step):
            q = 0
            for key in m.fs.flow_in_dict:
                if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
                    getattr(m.fs, key).conc_mass_in[0, 'tds'].fix(stash_value[q] * i)
                    q += 1

            run_water_tap(m=m, objective=False, skip_small=skip_small_sens)
            print(scenario, sum(stash_value) * i, 'LCOW -->', m.fs.costing.LCOW())

            lcow_list.append(value(m.fs.costing.LCOW))
            water_recovery_list.append(value(m.fs.costing.system_recovery))
            scenario_value.append(sum(stash_value) * i)
            scenario_name.append(scenario)
            elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
            elec_int.append(value(m.fs.costing.electricity_intensity))

        q = 0
        for key in m.fs.flow_in_dict:
            if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
                getattr(m.fs, key).conc_mass_in[0, 'tds'].fix(stash_value[q])
                q += 1

    ############################################################
    if m_scenario not in ['edr_ph_ro', 'ro_and_mf']:
        if m.fs.train['case_study'] in ['cherokee', 'gila_river']:
            print('skips RO sens')
        else:
            print('\n-------', 'RESET', '-------\n')
            run_water_tap(m=m, objective=False, skip_small=True)
            print('LCOW -->', m.fs.costing.LCOW())
            ############ inlet flow +-30% ############
            stash_value = []
            for key in m.fs.flow_in_dict:
                stash_value.append(value(getattr(m.fs, key).flow_vol_in[0]))
            scenario = 'Inlet Flow +-20%'
            print('-------', scenario, '-------')
            ub = 1.25
            lb = 0.75
            step = (ub - lb) / runs_per_scenario

            for i in np.arange(lb, ub + step, step):
                q = 0
                for key in m.fs.flow_in_dict:
                    getattr(m.fs, key).flow_vol_in[0].fix(stash_value[q] * i)
                    q += 1

                run_water_tap(m=m, objective=False, skip_small=skip_small_sens)
                print(scenario, stash_value[q - 1] * i, 'LCOW -->', m.fs.costing.LCOW())

                lcow_list.append(value(m.fs.costing.LCOW))
                water_recovery_list.append(value(m.fs.costing.system_recovery))
                scenario_value.append(i)
                scenario_name.append(scenario)
                elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
                elec_int.append(value(m.fs.costing.electricity_intensity))

            q = 0
            for key in m.fs.flow_in_dict:
                getattr(m.fs, key).flow_vol_in[0].fix(stash_value[q])
                q += 1

    ############################################################
    print('\n-------', 'RESET', '-------\n')
    run_water_tap(m=m, objective=False, skip_small=True)
    print('LCOW -->', m.fs.costing.LCOW())
    ############ lifetime years ############

    stash_value = value(m.fs.costing_param.plant_lifetime_yrs)
    scenario = 'Plant Lifetime 15-45 yrs'
    print('-------', scenario, '-------')
    ub = 45
    lb = 15
    step = (ub - lb) / runs_per_scenario
    for i in np.arange(lb, ub + step, step):
        m.fs.costing_param.plant_lifetime_yrs = i
        run_water_tap(m=m, objective=False, skip_small=True)
        print(scenario, i, 'LCOW -->', m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))

    m.fs.costing_param.plant_lifetime_yrs = stash_value
    ############################################################
    print('\n-------', 'RESET', '-------\n')
    run_water_tap(m=m, objective=False, skip_small=True)
    print('LCOW -->', m.fs.costing.LCOW())
    ############ elec cost +-30% ############

    stash_value = value(m.fs.costing_param.electricity_price)
    scenario = 'electricity price +- 30%'
    print('-------', scenario, '-------')
    ub = stash_value * 1.3
    lb = stash_value * 0.7
    step = (ub - lb) / runs_per_scenario
    for i in np.arange(lb, ub + step, step):
        m.fs.costing_param.electricity_price = i
        run_water_tap(m=m, objective=False, skip_small=True)
        print(scenario, i, 'LCOW -->', m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))

    m.fs.costing_param.electricity_price = stash_value

    ############################################################
    print('\n-------', 'RESET', '-------\n')
    run_water_tap(m=m, objective=False, skip_small=True)
    print('LCOW -->', m.fs.costing.LCOW())
    ############ lifetime years ############

    dwi_list = ['emwd', 'big_spring']
    if m.fs.train['case_study'] in dwi_list:
        for key in m.fs.pfd_dict.keys():
            if m.fs.pfd_dict[key]['Unit'] == 'deep_well_injection':

                stash_value = value(getattr(m.fs, key).lift_height[0])
                scenario = 'Injection Pressure LH 100-2000 ft'
                print('-------', scenario, '-------')
                ub = 2000
                lb = 100
                step = (ub - lb) / runs_per_scenario
                for i in np.arange(lb, ub + step, step):
                    getattr(m.fs, key).lift_height.fix(i)
                    run_water_tap(m=m, objective=False, skip_small=True)
                    print(scenario, i, 'LCOW -->', m.fs.costing.LCOW())

                    lcow_list.append(value(m.fs.costing.LCOW))
                    water_recovery_list.append(value(m.fs.costing.system_recovery))
                    scenario_value.append(i)
                    scenario_name.append(scenario)
                    elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
                    elec_int.append(value(m.fs.costing.electricity_intensity))

                getattr(m.fs, key).lift_height.fix(stash_value)

    ############################################################

    ############################################################
    print('\n-------', 'RESET', '-------\n')
    run_water_tap(m=m, objective=False, skip_small=True)
    print('LCOW -->', m.fs.costing.LCOW())
    ############ lifetime years ############
    area_list = []

    airtemp_list = ['cherokee', 'gila_river']
    if m.fs.train['case_study'] in airtemp_list:
        for key in m.fs.pfd_dict.keys():
            if m.fs.pfd_dict[key]['Unit'] == 'evaporation_pond':

                stash_value = value(getattr(m.fs, key).area[0])
                scenario = 'Area'
                print('-------', scenario, '-------')
                if m.fs.train['case_study'] == 'cherokee':
                    ub = 1.5
                    lb = 0.75
                if m.fs.train['case_study'] == 'gila_river':
                    lb = 0.5
                    ub = 1.05
                step = (ub - lb) / 50  # 50 runs
                for i in np.arange(lb, ub + step, step):
                    getattr(m.fs, key).area.fix(i * stash_value)
                    getattr(m.fs, key).water_recovery.unfix()
                    run_water_tap(m=m, objective=False, skip_small=True)
                    print(scenario, i * stash_value, 'LCOW -->', m.fs.costing.LCOW())

                    lcow_list.append(value(m.fs.costing.LCOW))
                    water_recovery_list.append(value(m.fs.costing.system_recovery))
                    scenario_value.append(i * stash_value)
                    scenario_name.append(scenario)
                    elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
                    elec_int.append(value(m.fs.costing.electricity_intensity))
                    area_list.append(value(m.fs.evaporation_pond.area[0]))

                getattr(m.fs, key).area.fix(stash_value)
                df_area = pd.DataFrame(area_list)
                df_area.to_csv('results/case_studies/area_list_%s_%s_%s.csv' % (
                        m.fs.train['case_study'], m_scenario, key))
    ############################################################    
    ############################################################
    print('\n-------', 'RESET', '-------\n')
    run_water_tap(m=m, objective=False, skip_small=True)
    print('LCOW -->', m.fs.costing.LCOW())
    ############ RO scenarios --> pressure % change, membrane area, replacement rate% ############

    if m_scenario not in ['edr_ph_ro', 'ro_and_mf']:
        if m.fs.train['case_study'] in ['cherokee', 'gila_river']:
            print('skips RO sens')
        else:
            for key in m.fs.pfd_dict.keys():
                if m.fs.pfd_dict[key]['Unit'] == 'reverse_osmosis':
                    if key in ro_list:
                        area = value(getattr(m.fs, key).membrane_area[0])
                        scenario_dict = {
                                'membrane_area': [-area * 0.2, area * 0.2],
                                'pressure': [0.85, 1.05],
                                'factor_membrane_replacement': [-0.1, 0.3]
                                }
                        for scenario in scenario_dict.keys():

                            print('\n-------', 'RESET', '-------\n')
                            run_water_tap(m=m, objective=False, skip_small=True)
                            print('LCOW -->', m.fs.costing.LCOW())

                            print('-------', scenario, '-------')
                            if scenario == 'pressure':
                                stash_value = value(getattr(getattr(getattr(m.fs, key), 'feed'), scenario)[0])
                                ub = stash_value * scenario_dict[scenario][1]
                                lb = stash_value * scenario_dict[scenario][0]
                            else:
                                stash_value = value(getattr(getattr(m.fs, key), scenario)[0])
                                ub = stash_value + scenario_dict[scenario][1]
                                lb = stash_value + scenario_dict[scenario][0]

                            step = (ub - lb) / runs_per_scenario

                            for i in np.arange(lb, ub + step, step):
                                if scenario == 'pressure':
                                    getattr(getattr(getattr(m.fs, key), 'feed'), scenario).fix(i)
                                else:
                                    getattr(getattr(m.fs, key), scenario).fix(i)

                                run_water_tap(m=m, objective=False, skip_small=skip_small_sens)
                                print(scenario, i, 'LCOW -->', m.fs.costing.LCOW())

                                lcow_list.append(value(m.fs.costing.LCOW))
                                water_recovery_list.append(value(m.fs.costing.system_recovery))
                                scenario_value.append(i)
                                scenario_name.append(key + '_' + scenario)
                                elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
                                elec_int.append(value(m.fs.costing.electricity_intensity))

                            if scenario == 'pressure':
                                getattr(getattr(getattr(m.fs, key), 'feed'), scenario).fix(stash_value)
                            else:
                                getattr(getattr(m.fs, key), scenario).fix(stash_value)

    ############################################################

    # final run to get baseline numbers again
    run_water_tap(m=m, objective=True, skip_small=skip_small_sens)

    sens_df['lcow'] = lcow_list
    sens_df['water_recovery'] = water_recovery_list
    sens_df['elec_lcow'] = elec_lcow
    sens_df['elec_int'] = elec_int
    sens_df['scenario_value'] = scenario_value
    sens_df['scenario_name'] = scenario_name
    sens_df['lcow_difference'] = sens_df.lcow - value(m.fs.costing.LCOW)
    sens_df['water_recovery_difference'] = (sens_df.water_recovery - value(m.fs.costing.system_recovery))
    sens_df['elec_lcow_difference'] = (sens_df.elec_lcow - value(m.fs.costing.elec_frac_LCOW))
    sens_df.elec_lcow = sens_df.elec_lcow * 100
    sens_df.water_recovery = sens_df.water_recovery * 100

    if save_results is True:
        sens_df.to_csv('results/case_studies/%s_%s_sensitivity.csv' % (case_study, m_scenario))
    if return_results is True:
        return sens_df


def print_ro_results(m):
    for key in m.fs.pfd_dict.keys():
        unit = str(key).replace('_', ' ').swapcase()
        if m.fs.pfd_dict[key]['Unit'] == 'reverse_osmosis':
            print(f'\n\tFeed pressure for {unit}: {round(getattr(m.fs, key).feed.pressure[0](), 2)} bar')
            print(f'\tMembrane area for {unit}: {round(getattr(m.fs, key).membrane_area[0](), 2)} m2')
            print(f'\tPure Water Flux for {unit}: {round(getattr(m.fs, key).pure_water_flux[0]() * 3600, 2)} LMH')
            print(f'\tA constant for {unit}: {round(getattr(m.fs, key).a[0](), 3)}')
            print(f'\tB constant for {unit}: {round(getattr(m.fs, key).b[0](), 3)}\n')
            print(f'\tRecovery for {unit}: {round(getattr(m.fs, key).water_recovery[0](), 3)}\n')

def print_ro_bounds(source_water_category, feed_flux_min, feed_flux_max, min_pressure, max_pressure, min_area, a=None, b=None):
    if source_water_category == 'seawater':
        print(f'\n\nSEAWATER for RO:'
              f'\n\tFlux [LMH] (min, max) = {feed_flux_min, feed_flux_max}'
              f'\n\tPressure [bar] (min, max) = {min_pressure, max_pressure}'
              f'\n\tMin. Area [m2] = {min_area}'
              f'\n\tWater Perm. [units] (min, max) = {a[0], a[1]}'
              f'\n\tSalt Perm. [units] (min, max) = {b[0], b[1]}\n\n')
    else:
        print(f'\n\nOTHER bounds for RO:'
              f'\n\tFlux [LMH] (min, max) = {feed_flux_min, feed_flux_max}'
              f'\n\tPressure [bar] (min, max) = {min_pressure, max_pressure}'
              f'\n\tMin. Area [m2] = {min_area}'
              f'\n\tWater Perm. [units] (min, max) = {a[0], a[1]}'
              f'\n\tSalt Perm. [units] (min, max) = {b[0], b[1]}\n\n')




# set reasonable bounds
def set_bounds(m=None, source_water_category=None):
    if source_water_category == 'seawater':
        feed_flux_max = 45  # lmh
        feed_flux_min = 10  # lmh
        a = [2, 7]
        b = [0.2, 0.7]
        max_pressure = 85
        min_area = 500
        min_pressure = 5
    else:
        feed_flux_max = 30  # lmh
        feed_flux_min = 8  # lmh
        a = [2, 7]
        b = [0.2, 0.7]
        max_pressure = 25
        min_area = 250
        min_pressure = 5

    print_ro_bounds(source_water_category, feed_flux_min, feed_flux_max, min_pressure, max_pressure, min_area, a=a, b=b)
    q = 1
    for key in m.fs.pfd_dict.keys():
        if m.fs.pfd_dict[key]['Unit'] == 'reverse_osmosis':

            setattr(m, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).pure_water_flux[0] * 3600 <= feed_flux_max)
                    )
            q += 1

            setattr(m, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).pure_water_flux[0] * 3600 >= feed_flux_min)
                    )
            q += 1

            setattr(m, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).membrane_area[0] >= min_area)
                    )
            q += 1

            setattr(m, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).feed.pressure[0] <= max_pressure)
                    )
            q += 1

            setattr(m.fs, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).a[0] <= a[1])
                    )
            q += 1
            setattr(m.fs, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).a[0] >= a[0])
                    )

            setattr(m.fs, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).b[0] <= b[1])
                    )
            q += 1
            setattr(m.fs, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).b[0] >= b[0])
                    )

            q += 1

    run_water_tap(m=m, objective=True, skip_small=True)

    return m


# set reasonable bounds
def unset_bounds(m=None):
    print('\nRemoving bounds for RO...\n')
    feed_flux_max = 85  # lmh
    feed_flux_min = 0.01  # lmh
    a = [0.01, 99]
    b = [0.01, 99]
    max_pressure = 93
    min_area = 100
    min_pressure = 5

    q = 1
    for key in m.fs.pfd_dict.keys():
        if m.fs.pfd_dict[key]['Unit'] == 'reverse_osmosis':

            setattr(m, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).pure_water_flux[0] * 3600 <= feed_flux_max)
                    )
            q += 1

            setattr(m, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).pure_water_flux[0] * 3600 >= feed_flux_min)
                    )
            q += 1

            setattr(m, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).membrane_area[0] >= min_area)
                    )
            q += 1
            setattr(m.fs, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).a[0] <= a[1])
                    )
            q += 1
            setattr(m.fs, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).a[0] >= a[0])
                    )

            setattr(m.fs, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).b[0] <= b[1])
                    )
            q += 1
            setattr(m.fs, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).b[0] >= b[0])
                    )
            q += 1

    return m


def run_water_tap_ro(m, source_water_category=None, return_df=False, skip_small=None, desired_recovery=0, ro_bounds=None, source_scenario=None, scenario_name=None):
    scenario = scenario_name
    case_study = m.fs.train['case_study']
    reference = m.fs.train['reference']
    case_study_print = case_study.replace('_', ' ').swapcase()
    scenario_print = scenario.replace('_', ' ').swapcase()

    has_ro = False
    for key in m.fs.pfd_dict.keys():
        unit = str(key).replace('_', ' ').swapcase()
        if m.fs.pfd_dict[key]['Unit'] == 'reverse_osmosis':
            getattr(m.fs, key).feed.pressure.unfix()
            getattr(m.fs, key).membrane_area.unfix()
            print(f'\nUnfixing feed pressure and area for {unit}...\n')
            has_ro = True

    if case_study == 'irwin':
        m.fs.reverse_osmosis.feed.pressure.fix(30)

    print(f'Case Study = {case_study_print}\nScenario = {scenario_print}\n')
    run_water_tap(m=m, objective=True, skip_small=skip_small)

    print_ro_results(m)

    if case_study == 'irwin':
        m.fs.reverse_osmosis.feed.pressure.unfix()
    #
    if case_study == 'upw':

        m.fs.media_filtration.water_recovery.fix(0.9)
        m.fs.reverse_osmosis.eq1_upw = Constraint(expr=m.fs.reverse_osmosis.flow_vol_out[0] <= 0.05678 * 1.01)
        m.fs.reverse_osmosis.eq3_upw = Constraint(expr=m.fs.reverse_osmosis.flow_vol_waste[0] <= 0.04416 * 1.01)
        m.fs.reverse_osmosis.eq4_upw = Constraint(expr=m.fs.reverse_osmosis.flow_vol_waste[0] >= 0.04416 * 0.99)
        m.fs.reverse_osmosis_2.eq1_upw = Constraint(expr=m.fs.reverse_osmosis_2.flow_vol_out[0] <= (0.5 * m.fs.reverse_osmosis_2.flow_vol_in[0]) * 1.01)
        m.fs.ro_stage.eq1_upw = Constraint(expr=m.fs.ro_stage.flow_vol_out[0] <= 0.03155 * 1.01)
        m.fs.ro_stage.eq2_upw = Constraint(expr=m.fs.ro_stage.flow_vol_out[0] >= 0.03155 * 0.99)

    if case_study == 'uranium':

        m.fs.ro_production.eq1_anna = Constraint(expr=m.fs.ro_production.flow_vol_out[0] <= (0.7 * m.fs.ro_production.flow_vol_in[0]) * 1.01)
        m.fs.ro_production.eq2_anna = Constraint(expr=m.fs.ro_production.flow_vol_out[0] >= (0.7 * m.fs.ro_production.flow_vol_in[0]) * 0.99)
        m.fs.ro_restore_stage.eq3_anna = Constraint(expr=m.fs.ro_restore_stage.flow_vol_out[0] <= (0.5 * m.fs.ro_restore_stage.flow_vol_in[0]) * 1.01)
        m.fs.ro_restore_stage.eq4_anna = Constraint(expr=m.fs.ro_restore_stage.flow_vol_out[0] >= (0.5 * m.fs.ro_restore_stage.flow_vol_in[0]) * 0.99)
        m.fs.ro_restore.eq5_anna = Constraint(expr=m.fs.ro_restore.flow_vol_out[0] <= (0.75 * m.fs.ro_restore.flow_vol_in[0]) * 1.01)
        m.fs.ro_restore.eq6_anna = Constraint(expr=m.fs.ro_restore.flow_vol_out[0] >= (0.75 * m.fs.ro_restore.flow_vol_in[0]) * 0.99)

    if case_study == 'gila_river':
        if 'reverse_osmosis' in m.fs.pfd_dict.keys():

            m.fs.reverse_osmosis.kurby1 = Constraint(expr=m.fs.reverse_osmosis.flow_vol_out[0] <= (0.59 * m.fs.reverse_osmosis.flow_vol_in[0]) * 1.01)
            m.fs.reverse_osmosis.kurby2 = Constraint(expr=m.fs.reverse_osmosis.flow_vol_out[0] >= (0.59 * m.fs.reverse_osmosis.flow_vol_in[0]) * 0.99)

    if case_study == 'cherokee':
        if 'reverse_osmosis' in m.fs.pfd_dict.keys():

            m.fs.reverse_osmosis.kurby1 = Constraint(expr=m.fs.reverse_osmosis.flow_vol_out[0] <= (0.98 * m.fs.reverse_osmosis.flow_vol_in[0]) * 1.01)
            m.fs.reverse_osmosis.kurby2 = Constraint(expr=m.fs.reverse_osmosis.flow_vol_out[0] >= (0.98 * m.fs.reverse_osmosis.flow_vol_in[0]) * 0.99)

    if case_study == 'san_luis':
        if scenario in ['baseline', 'dwi']:
            m.fs.reverse_osmosis_1.feed.pressure.fix(25.5)
            m.fs.reverse_osmosis_2.feed.pressure.fix(36)

    if has_ro:
        m = set_bounds(m, source_water_category=ro_bounds)
        print_ro_results(m)

    if desired_recovery < 1:
        if m.fs.costing.system_recovery() > desired_recovery:
            print('Running for desired recovery -->', desired_recovery)
            m.fs.recovery_bound = Constraint(expr=m.fs.costing.system_recovery <= desired_recovery)
            m.fs.recovery_bound1 = Constraint(
                    expr=m.fs.costing.system_recovery >= desired_recovery - 1.5)

            if scenario_name == 'baseline':
                run_water_tap(m=m, objective=True, skip_small=skip_small)
            else:
                run_water_tap(m=m, objective=True, skip_small=skip_small, print_model_results='summary')

            print_ro_results(m)

        else:
            print('System recovery already lower than desired recovery.'
                  '\n\tDesired:', desired_recovery,
                  '\n\tCurrent:', m.fs.costing.system_recovery())
    ur_list = []

    if case_study == 'uranium':
        ur_list.append(m.fs.ion_exchange.removal_fraction[0, 'tds']())
        ur_list.append(m.fs.ion_exchange.anion_res_capacity[0]())
        ur_list.append(m.fs.ion_exchange.cation_res_capacity[0]())

        # change this to set splitters
    upw_list = []
    if case_study == 'upw':
        upw_list.append(m.fs.splitter2.split_fraction_outlet3[0]())
        upw_list.append(m.fs.splitter2.split_fraction_outlet4[0]())

    scenario_name = m.fs.train['scenario']

    if has_ro:
        ro_stash = {}
        for key in m.fs.pfd_dict.keys():
            if m.fs.pfd_dict[key]['Unit'] == 'reverse_osmosis':
                ro_stash[key] = {
                        'feed.pressure': getattr(m.fs, key).feed.pressure[0](),
                        'membrane_area': getattr(m.fs, key).membrane_area[0](),
                        'a': getattr(m.fs, key).a[0](),
                        'b': getattr(m.fs, key).b[0]()
                        }

        ###### RESET BOUNDS AND DOUBLE CHECK RUN IS OK SO CAN GO INTO SENSITIVITY #####
        print('\nRebuilding model, running with unfixed, then fixed RO based on model results...\n')
        m = watertap_setup(dynamic=False, case_study=case_study, reference=reference,
                           scenario=scenario, source_scenario=source_scenario)

        m = get_case_study(m=m)

        for key in m.fs.pfd_dict.keys():
            unit = str(key).replace('_', ' ').swapcase()
            if m.fs.pfd_dict[key]['Unit'] == 'reverse_osmosis':
                getattr(m.fs, key).feed.pressure.unfix()
                getattr(m.fs, key).membrane_area.unfix()
                print('Unfixing feed pressure and area for', unit, '...\n')

        if case_study == 'irwin':
            m.fs.reverse_osmosis.feed.pressure.fix(30)

        if case_study == 'upw':
            m.fs.media_filtration.water_recovery.fix(0.9)
            m.fs.splitter2.split_fraction_outlet3.fix(upw_list[0])
            m.fs.splitter2.split_fraction_outlet4.fix(upw_list[1])

        if case_study == 'uranium':
            m.fs.ion_exchange.removal_fraction[0, 'tds'].fix(ur_list[0])
            m.fs.ion_exchange.anion_res_capacity.fix(ur_list[1])
            m.fs.ion_exchange.cation_res_capacity.fix(ur_list[2])

        run_water_tap(m=m, objective=True, skip_small=skip_small, print_model_results='summary')

        m.fs.objective_function.deactivate()

        for key in m.fs.pfd_dict.keys():
            if m.fs.pfd_dict[key]['Unit'] == 'reverse_osmosis':
                getattr(m.fs, key).feed.pressure.fix(ro_stash[key]['feed.pressure'])
                getattr(m.fs, key).membrane_area.fix(ro_stash[key]['membrane_area'])
                getattr(m.fs, key).a.fix(ro_stash[key]['a'])
                getattr(m.fs, key).b.fix(ro_stash[key]['b'])

    run_water_tap(m=m, objective=False, print_model_results='summary', skip_small=True)

    print_ro_results(m)

    df = get_results_table(m=m, case_study=m.fs.train['case_study'], scenario=scenario_name)

    if return_df is True:
        return m, df
    else:
        return m