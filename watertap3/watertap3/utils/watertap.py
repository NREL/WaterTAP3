import ast
import logging
import warnings

import numpy as np
import pandas as pd
from idaes.core import FlowsheetBlock
from idaes.core.util.model_statistics import degrees_of_freedom
import os
from pyomo.environ import Var, Expression, NonNegativeReals, Block, ConcreteModel, Constraint, Objective, SolverFactory, TransformationFactory, units as pyunits, value
from pyomo.network import SequentialDecomposition, Arc
from pyomo.network.port import SimplePort
# from pyomo.contrib.mindtpy.MindtPy import MindtPySolver
from . import financials
from .case_study_trains import *
from .post_processing import get_results_table

warnings.filterwarnings('ignore')

__all__ = ['run_water_tap', 'watertap_setup', 'run_model', 'run_water_tap', 'run_water_tap_ro',
           'run_sensitivity', 'print_ro_results', 'print_results', 'set_bounds',
           'run_sensitivity_power']


def run_water_tap(m=None, solver_results=False, print_model_results=False, objective=False,
                  max_attempts=3, initialize_flow=5, skip_small=True, return_solution=False,
                  sensitivity_flow=None):
    # if flow is small it resets the flow to any inlet as 2 m3/s
    if skip_small == False:
        for key in m.fs.flow_in_dict.keys():
            getattr(m.fs, key).flow_vol_in.fix(initialize_flow)
            small_flow = True

        # if flow is small it runs the model twice at most. then runs again with actual flows
        if small_flow:
            print('Flow is relatively small (< 1 m3/s). Running model with larger dummy flows to initialize...\n')
            run_model(m=m, solver_results=False, objective=False, max_attempts=1)
            print('Model finished running to initialize conditions. Now running with actual flow...\n')
            for key in m.fs.flow_in_dict.keys():
                if sensitivity_flow is None:
                    getattr(m.fs, key).flow_vol_in.fix(m.fs.flow_in_dict[key])
                else:
                    getattr(m.fs, key).flow_vol_in.fix(sensitivity_flow[key])

            run_model(m=m, solver_results=solver_results, objective=objective, max_attempts=max_attempts)

        else:
            run_model(m=m, solver_results=solver_results, objective=objective, max_attempts=max_attempts)

    else:
        run_model(m=m, solver_results=solver_results, objective=objective, max_attempts=max_attempts)

    if print_model_results:
        print_results(m, print_model_results)


def watertap_setup(dynamic=False, case_study=None, reference='nawi', scenario=None,
                   source_reference=None, source_case_study=None, source_scenario=None):
    m = ConcreteModel()

    m.fs = FlowsheetBlock(default={
            'dynamic': dynamic
            })

    m.fs.train = {
            'case_study': case_study,
            'reference': reference,
            'scenario': scenario
            }

    if source_reference is None:
        source_reference = reference
    if source_case_study is None:
        source_case_study = case_study
    if source_scenario is None:
        source_scenario = scenario

    df = pd.read_csv('data/treatment_train_setup.csv')

    df = filter_df(df, m)
    water_type_list = []

    for i in list(df[df.Type == 'intake'].index):
        for water_type in ast.literal_eval(df[df.Type == 'intake'].loc[i]['Parameter'])['water_type']:
            water_type_list.append(water_type)

    if len(water_type_list) == 1:
        water_type_list = water_type_list[0]

    m.fs.source_water = {
            'case_study': source_case_study,
            'reference': source_reference,
            'scenario': source_scenario,
            'water_type': water_type_list
            }

    return m


def run_model(m=None, solver_results=False, objective=False, max_attempts=0, return_solution=False):
    financials.get_system_costing(m.fs)

    TransformationFactory('network.expand_arcs').apply_to(m)
    seq = SequentialDecomposition()
    G = seq.create_graph(m)

    if objective == True:
        # obj = Expression(expr=1E6 * (m.fs.costing.capital_investment_total * m.fs.costing.capital_recovery_factor + m.fs.costing.operating_cost_annual) * (m.fs.costing.treated_water * 3600 * 24 * 365 * m.fs.costing_param.plant_cap_utilization) ** -1)
        # m.fs.objective_function = Objective(expr=obj)


        m.fs.objective_function = Objective(expr=m.fs.costing.LCOW)

    solver = SolverFactory('ipopt')
    # m.fs.solver = solver = SolverFactory('mindtpy')

    logging.getLogger('pyomo.core').setLevel(logging.ERROR)
    print('----------------------------------------------------------------------')
    print('\nDegrees of Freedom:', degrees_of_freedom(m))

    results = solver.solve(m, tee=solver_results)
    # m.fs.results = results = solver.solve(m, mip_solver='glpk', nlp_solver='ipopt', tee=True)

    attempt_number = 1
    while ((results.solver.termination_condition in ['infeasible', 'maxIterations']) & (attempt_number <= max_attempts)):
        print(f'\nAttempt {attempt_number}')
        print('\nWaterTAP3 solver returned %s solution...\n' % results.solver.termination_condition)
        print(f'Running again with updated initial conditions --- attempt {attempt_number}\n')
        results = solver.solve(m, tee=solver_results)
        attempt_number += 1

    print('\nWaterTAP3 solution', results.solver.termination_condition, '\n')
    print('----------------------------------------------------------------------')

    if results.solver.termination_condition in ['infeasible', 'maxIterations']:
        print('\nWaterTAP3 solver returned %s solution. Check option to run model with updated initial conditions.\n\n' % results.solver.termination_condition)
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
    print('Total Capital Investment ($MM)', round(value(m.fs.costing.capital_investment_total()), 3))
    print('Annual Fixed Operating Cost ($MM/yr)', round(value(m.fs.costing.fixed_op_cost_annual()), 3))
    print('Annual Catalysts and Chemicals Cost ($MM/yr)', round(value(m.fs.costing.cat_and_chem_cost_annual()), 3))
    print('Annual Electricity Costs ($MM/yr)', round(value(m.fs.costing.electricity_cost_annual()), 3))
    print('Annual Other Variable Costs ($MM/yr)', round(value(m.fs.costing.other_var_cost_annual()), 3))
    print('Annual Operating Costs ($MM/yr)', round(value(m.fs.costing.operating_cost_annual()), 3))
    print('Treated water (m3/s) --->', round(value(m.fs.costing.treated_water()), 3))
    print('Total water recovery (%) --->', round(value(100 * m.fs.costing.system_recovery()), 3))
    print('Electricity intensity (kWh/m3) ---> ', round(value(m.fs.costing.electricity_intensity()), 3))
    print('LCOW ($/m3) ---> ', round(value(m.fs.costing.LCOW()), 3))
    print('Electricity portion of LCOW (%) --->', round(value(100 * m.fs.costing.elec_frac_LCOW()), 3))
    print('----------------------------------------------------------------------')


def run_sensitivity_power(m=None, save_results=False, return_results=False, scenario=None,
                          case_study=None, skip_small_sens=True):
    ro_list = ['reverse_osmosis', 'ro_first_pass', 'ro_a1', 'ro_b1', 'ro_active', 'ro_restore']

    sens_df = pd.DataFrame()

    m_scenario = scenario

    m.fs.lcow_list = lcow_list = []
    m.fs.water_recovery_list = water_recovery_list = []
    m.fs.scenario_value = scenario_value = []
    m.fs.scenario_name = scenario_name = []
    m.fs.elec_lcow = elec_lcow = []
    m.fs.elec_int = elec_int = []
    m.fs.treated_water = treated_water = []
    m.fs.bc_elec = bc_elec = []
    m.fs.ro_elec = ro_elec = []

    m.fs.ro_a_pressure = ro_a_pressure = []
    m.fs.ro_a_elect_int = ro_a_elect_int = []
    m.fs.ro_a_elect_cost = ro_a_elect_cost = []
    m.fs.ro_a_recovery = ro_a_recovery = []
    m.fs.ro_a_capital = ro_a_capital = []
    m.fs.ro_a_om = ro_a_om = []
    m.fs.ro_a_flow_in = ro_a_flow_in = []
    m.fs.ro_a_flow_out = ro_a_flow_out = []
    m.fs.ro_a_area = ro_a_area = []
    m.fs.ro_a_tds_in = ro_a_tds_in = []
    m.fs.ro_a_tds_out = ro_a_tds_out = []
    m.fs.ro_a_flux = ro_a_flux = []
    m.fs.ro_a_mass_h2o = ro_a_mass_h2o = []
    m.fs.ro_a_f_osm = ro_a_f_osm = []
    m.fs.ro_a_r_osm = ro_a_r_osm = []
    m.fs.ro_a_mass_tds = ro_a_mass_tds = []
    m.fs.ro_a_salt_rej = ro_a_salt_rej = []
    m.fs.landfill_zld_tds = landfill_zld_tds = []

    m.fs.ro_pressure = ro_pressure = []
    m.fs.ro_elect_int = ro_elect_int = []
    m.fs.ro_elect_cost = ro_elect_cost = []
    m.fs.ro_recovery = ro_recovery = []
    m.fs.sys_elec = sys_elec = []
    m.fs.sys_elec_int = sys_elec_int = []
    m.fs.evap_flow_out = evap_flow_out = []
    m.fs.evap_flow_waste = evap_flow_waste = []
    m.fs.evap_capital = evap_capital = []
    m.fs.dis_elect_int = dis_elect_int = []
    m.fs.area_list = area_list = []

    if m.fs.train['case_study'] == "cherokee" and m_scenario == "zld_ct":
        if 'reverse_osmosis_a' in m.fs.pfd_dict.keys():
            stash_value = value(getattr(m.fs, 'evaporation_pond').area[0])
            scenario = 'Area'
            sens_var = 'evap_pond_area'
            print('-------', scenario, '-------')
            lb = 0.45
            ub = 0.96
            step = (ub - lb) / 50  # 50 runs
            getattr(m.fs, 'evaporation_pond').water_recovery.fix(0.9)
            getattr(m.fs, 'evaporation_pond').area.unfix()
            m.fs.reverse_osmosis_a.feed.pressure.unfix()
            m.fs.reverse_osmosis_a.membrane_area.unfix()

            for recovery_rate in np.arange(lb, ub, step):
                m.fs.reverse_osmosis_a.kurby4 = Constraint(expr=m.fs.reverse_osmosis_a.flow_vol_out[0] <= (recovery_rate * m.fs.reverse_osmosis_a.flow_vol_in[0]))

                run_water_tap(m=m, objective=True, skip_small=True)
                print(scenario, recovery_rate, 'LCOW -->', m.fs.costing.LCOW())

                # print('evap pond recovery:', getattr(m.fs, 'evaporation_pond').water_recovery[0]())
                # print('evap pond area:', getattr(m.fs, 'evaporation_pond').area[0]())
                # print('RO recovery:', m.fs.reverse_osmosis_a.flow_vol_out[0]() / m.fs.reverse_osmosis_a.flow_vol_in[0]())

                lcow_list.append(value(m.fs.costing.LCOW))
                water_recovery_list.append(value(m.fs.costing.system_recovery))
                scenario_value.append(recovery_rate)
                scenario_name.append(scenario)
                elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
                elec_int.append(value(m.fs.costing.electricity_intensity))
                area_list.append(value(m.fs.evaporation_pond.area[0]))
                treated_water.append(m.fs.costing.treated_water())
                ro_a_elect_cost.append(m.fs.reverse_osmosis_a.costing.electricity_cost())
                ro_a_elect_int.append(m.fs.reverse_osmosis_a.electricity())
                ro_a_pressure.append(m.fs.reverse_osmosis_a.feed.pressure[0]())

                ro_a_recovery.append(m.fs.reverse_osmosis_a.ro_recovery())
                ro_a_capital.append(m.fs.reverse_osmosis_a.costing.total_cap_investment())
                ro_a_om.append(m.fs.reverse_osmosis_a.costing.annual_op_main_cost())
                ro_a_flow_in.append(m.fs.reverse_osmosis_a.flow_vol_in[0]())
                ro_a_flow_out.append(m.fs.reverse_osmosis_a.flow_vol_out[0]())
                ro_a_area.append(m.fs.reverse_osmosis_a.membrane_area[0]())
                ro_a_tds_in.append(m.fs.reverse_osmosis_a.conc_mass_in[0, 'tds']())
                ro_a_tds_out.append(m.fs.reverse_osmosis_a.conc_mass_out[0, 'tds']())
                ro_a_flux.append(m.fs.reverse_osmosis_a.flux_lmh())
                ro_a_mass_h2o.append(m.fs.reverse_osmosis_a.permeate.mass_flow_H2O[0]())
                ro_a_f_osm.append(m.fs.reverse_osmosis_a.feed.pressure_osm[0]())
                ro_a_r_osm.append(m.fs.reverse_osmosis_a.retentate.pressure_osm[0]())
                ro_a_mass_tds.append(m.fs.reverse_osmosis_a.permeate.mass_flow_tds[0]())
                ro_a_salt_rej.append(m.fs.reverse_osmosis_a.salt_rejection_conc())

                landfill_zld_tds.append(m.fs.landfill_zld.conc_mass_in[0, 'tds']())
                ro_elect_cost.append(m.fs.reverse_osmosis.costing.electricity_cost())
                ro_pressure.append(m.fs.reverse_osmosis.feed.pressure[0]())
                ro_elect_int.append(m.fs.reverse_osmosis.electricity())
                ro_recovery.append(m.fs.reverse_osmosis.ro_recovery())
                dis_elect_int.append(m.fs.discharge.electricity())
                sys_elec.append(m.fs.costing.electricity_cost_annual())
                sys_elec_int.append(m.fs.costing.electricity_intensity())
                evap_flow_out.append(m.fs.evaporation_pond.flow_vol_out[0]())
                evap_flow_waste.append(m.fs.evaporation_pond.flow_vol_waste[0]())
                evap_capital.append(m.fs.evaporation_pond.costing.total_cap_investment())

                # print('Electricity intensity', elec_int[-1])
                # print('Electricity intensity RO:', m.fs.reverse_osmosis_a.costing.elec_int_treated())
                # print('Electricity cost RO-A:', m.fs.reverse_osmosis_a.costing.electricity_cost())
                # print('Electricity intensity RO-B:', m.fs.reverse_osmosis.electricity())
                # print('Treated water:', m.fs.costing.treated_water())
                # print('Area', area_list)
                # print_ro_results(m)
            getattr(m.fs, 'evaporation_pond').water_recovery.unfix()
            getattr(m.fs, 'evaporation_pond').area.fix(stash_value)

    if m.fs.train['case_study'] == "gila_river" and m_scenario == "baseline":
        if 'reverse_osmosis' in m.fs.pfd_dict.keys():
            stash_value = value(getattr(m.fs, 'evaporation_pond').area[0])
            scenario = 'Area'
            sens_var = 'evap_pond_area'
            print('-------', scenario, '-------')

            lb = 0.45
            ub = 0.90
            step = (ub - lb) / 50  # 50 runs
            getattr(m.fs, 'evaporation_pond').water_recovery.fix(0.9)
            getattr(m.fs, 'evaporation_pond').area.unfix()

            m.fs.reverse_osmosis.feed.pressure.unfix()
            m.fs.reverse_osmosis.membrane_area.unfix()

            for recovery_rate in np.arange(lb, ub, step):
                m.fs.reverse_osmosis.kurby4 = Constraint(expr=m.fs.reverse_osmosis.flow_vol_out[0] <= (recovery_rate * m.fs.reverse_osmosis.flow_vol_in[0]))

                m.fs.brine_concentrator.water_recovery.fix(recovery_rate)

                run_water_tap(m=m, objective=True, skip_small=True)
                print(scenario, recovery_rate, 'LCOW -->', m.fs.costing.LCOW())

                print('evap pond recovery:', getattr(m.fs, 'evaporation_pond').water_recovery[0]())
                print('evap pond area:', getattr(m.fs, 'evaporation_pond').area[0]())
                print('RO recovery:', m.fs.reverse_osmosis.flow_vol_out[0]() / m.fs.reverse_osmosis.flow_vol_in[0]())
                lcow_list.append(value(m.fs.costing.LCOW))
                water_recovery_list.append(value(m.fs.costing.system_recovery))
                scenario_value.append(recovery_rate)
                scenario_name.append(scenario)
                elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
                elec_int.append(value(m.fs.costing.electricity_intensity))
                area_list.append(value(m.fs.evaporation_pond.area[0]))
                treated_water.append(m.fs.costing.treated_water())
                ro_a_elect_cost.append(m.fs.costing.electricity_cost_annual())
                bc_elec.append(m.fs.brine_concentrator.costing.electricity_cost())
                ro_elec.append(m.fs.reverse_osmosis.costing.electricity_cost())
                sys_elec.append(m.fs.costing.electricity_cost_annual())
                sys_elec_int.append(m.fs.costing.electricity_intensity())

            getattr(m.fs, 'evaporation_pond').water_recovery.unfix()
            getattr(m.fs, 'evaporation_pond').area.fix(stash_value)

    ############################################################
    # final run to get baseline numbers again
    print('\n-------', 'RESET', '-------\n')
    run_water_tap(m=m, objective=False, skip_small=True)
    print('LCOW -->', m.fs.costing.LCOW())

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
    sens_df['area'] = area_list
    sens_df.elec_lcow = sens_df.elec_lcow * 100
    sens_df.water_recovery = sens_df.water_recovery * 100

    if save_results:
        sens_df.to_csv('results/case_studies/area_%s_%s_sensitivity.csv' % (case_study, m_scenario), index=False)
    if return_results:
        return sens_df


def run_sensitivity(m=None, save_results=False, return_results=False, scenario=None,
                    case_study=None, skip_small_sens=True):

    print('\n==================== STARTING SENSITIVITY ANALYSIS ===================\n')

    ro_list = ['reverse_osmosis', 'ro_first_pass', 'ro_a1', 'ro_b1',
               'ro_active', 'ro_restore', 'ro_first_stage']

    sens_df = pd.DataFrame()

    m_scenario = scenario
    case_print = m.fs.train['case_study'].replace('_', ' ').swapcase()
    scenario_print = m.fs.train['scenario'].replace('_', ' ').swapcase()

    m.fs.lcow_list = lcow_list = []
    m.fs.water_recovery_list = water_recovery_list = []
    m.fs.scenario_value = scenario_value = []
    m.fs.scenario_name = scenario_name = []
    m.fs.elec_lcow = elec_lcow = []
    m.fs.elec_int = elec_int = []
    m.fs.baseline_sens_value = baseline_sens_value = []
    m.fs.baseline_lcows = baseline_lcows = []
    m.fs.baseline_elect_ints = baseline_elect_ints = []
    m.fs.lcow_norm = lcow_norm = []
    m.fs.lcow_diff = lcow_diff = []
    m.fs.sens_vars = sens_vars = []
    m.fs.treated_water = treated_water = []
    m.fs.treated_water_norm = treated_water_norm = []
    m.fs.elect_int_norm = elect_int_norm = []
    m.fs.sens_var_norm = sens_var_norm = []
    m.fs.ro_pressure = ro_pressure = []
    m.fs.ro_press_norm = ro_press_norm = []
    m.fs.ro_area = ro_area = []
    m.fs.ro_area_norm = ro_area_norm = []
    m.fs.mem_replacement = mem_replacement = []

    baseline_treated_water = value(m.fs.costing.treated_water)
    baseline_lcow = value(m.fs.costing.LCOW)
    baseline_elect_int = value(m.fs.costing.electricity_intensity)

    lcow_list.append(value(m.fs.costing.LCOW))
    water_recovery_list.append(value(m.fs.costing.system_recovery))
    scenario_value.append('baseline')
    scenario_name.append(scenario)
    elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
    elec_int.append(value(m.fs.costing.electricity_intensity))
    baseline_sens_value.append(np.nan)
    baseline_lcows.append(baseline_lcow)
    baseline_elect_ints.append(baseline_elect_int)
    lcow_norm.append(1)
    lcow_diff.append(0)
    sens_vars.append('baseline')
    treated_water.append(value(m.fs.costing.treated_water))
    treated_water_norm.append(1)
    elect_int_norm.append(1)
    sens_var_norm.append(1)
    mem_replacement.append(None)
    ro_pressure.append(None)
    ro_press_norm.append(None)
    ro_area.append(None)
    ro_area_norm.append(None)

    runs_per_scenario = 20

    ############ Plant Capacity Utilization 70-100% ############
    stash_value = m.fs.costing_param.plant_cap_utilization
    scenario = 'Plant Capacity Utilization 70-100%'
    sens_var = 'plant_cap'
    print('-------', scenario, '-------')
    ub = 1
    lb = 0.7
    step = (ub - lb) / runs_per_scenario
    for i in np.arange(lb, ub + step, step):

        m.fs.costing_param.plant_cap_utilization = i

        run_water_tap(m=m, objective=False, skip_small=True)

        print('\n===============================')
        print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
        print('===============================\n')
        print(scenario, i * 100, 'LCOW -->', m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i * 100)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))
        baseline_sens_value.append(stash_value)
        baseline_lcows.append(baseline_lcow)
        baseline_elect_ints.append(baseline_elect_int)
        lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
        lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
        sens_vars.append(sens_var)
        treated_water.append(value(m.fs.costing.treated_water))
        treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
        elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
        sens_var_norm.append(i / stash_value)
        ro_pressure.append(None)
        ro_press_norm.append(None)
        ro_area.append(None)
        ro_area_norm.append(None)
        mem_replacement.append(None)

    m.fs.costing_param.plant_cap_utilization = stash_value
    ############################################################

    print('\n-------', 'RESET', '-------\n')
    run_water_tap(m=m, objective=False, skip_small=True)
    print('LCOW -->', m.fs.costing.LCOW())

    ############ WACC 5-10%############
    stash_value = m.fs.costing_param.wacc
    scenario = 'Weighted Average Cost of Capital 5-10%'
    sens_var = 'wacc'
    print('-------', scenario, '-------')
    ub = stash_value + 0.05
    lb = stash_value
    step = (ub - lb) / runs_per_scenario
    for i in np.arange(lb, ub + step, step):
        print('\n===============================')
        print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
        print('===============================\n')
        m.fs.costing_param.wacc = i
        run_water_tap(m=m, objective=False, skip_small=True)
        print(scenario, i * 100, 'LCOW -->', m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i * 100)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))
        baseline_sens_value.append(stash_value)
        baseline_lcows.append(baseline_lcow)
        baseline_elect_ints.append(baseline_elect_int)
        lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
        lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
        sens_vars.append(sens_var)
        treated_water.append(value(m.fs.costing.treated_water))
        treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
        elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
        sens_var_norm.append(i / stash_value)
        ro_pressure.append(None)
        ro_press_norm.append(None)
        ro_area.append(None)
        ro_area_norm.append(None)
        mem_replacement.append(None)

    m.fs.costing_param.wacc = stash_value
    ############################################################

    tds_in = False

    for key in m.fs.flow_in_dict:
        if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
            tds_in = True

    if tds_in:
        print('\n-------', 'RESET', '-------\n')
        run_water_tap(m=m, objective=False, skip_small=True)
        print('LCOW -->', m.fs.costing.LCOW())

        ############ Salinity +/- 30% ############
        stash_value = []
        tds_list = []
        for key in m.fs.flow_in_dict:
            if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
                stash_value.append(value(getattr(m.fs, key).conc_mass_in[0, 'tds']))
        print(stash_value)
        scenario = 'Inlet TDS +-25%'
        sens_var = 'tds_in'
        print('-------', scenario, '-------')
        ub = 1.25
        lb = 0.75

        # if m_scenario in ['edr_ph_ro', 'ro_and_mf']:
        #     print('redoing upper and lower bounds')
        #     ub = 80
        #     lb = 60

        step = (ub - lb) / runs_per_scenario

        for i in np.arange(lb, ub + step, step):
            q = 0
            for key in m.fs.flow_in_dict:
                if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
                    getattr(m.fs, key).conc_mass_in[0, 'tds'].fix(stash_value[q] * i)
                    q += 1
            print('\n===============================')
            print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
            print('===============================\n')
            run_water_tap(m=m, objective=False, skip_small=skip_small_sens)
            print(scenario, sum(stash_value) * i, 'LCOW -->', m.fs.costing.LCOW())

            lcow_list.append(value(m.fs.costing.LCOW))
            water_recovery_list.append(value(m.fs.costing.system_recovery))
            scenario_value.append(sum(stash_value) * i)
            scenario_name.append(scenario)
            elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
            elec_int.append(value(m.fs.costing.electricity_intensity))
            baseline_sens_value.append(sum(stash_value))
            baseline_lcows.append(baseline_lcow)
            baseline_elect_ints.append(baseline_elect_int)
            lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
            lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
            sens_vars.append(sens_var)
            treated_water.append(value(m.fs.costing.treated_water))
            treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
            elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
            sens_var_norm.append(i)
            ro_pressure.append(None)
            ro_press_norm.append(None)
            ro_area.append(None)
            ro_area_norm.append(None)
            mem_replacement.append(None)

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
            ############ inlet flow +-25% ############
            m.fs.stash_value = stash_value = []
            for key in m.fs.flow_in_dict:
                stash_value.append(value(getattr(m.fs, key).flow_vol_in[0]))
            scenario = 'Inlet Flow +-25%'
            sens_var = 'flow_in'
            print('-------', scenario, '-------')
            ub = 1.25
            lb = 0.75
            step = (ub - lb) / runs_per_scenario

            for i in np.arange(lb, ub + step, step):
                # q = 0
                for q, key in enumerate(m.fs.flow_in_dict.keys()):
                    getattr(m.fs, key).flow_vol_in[0].fix(stash_value[q] * i)  # q += 1
                print('\n===============================')
                print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
                print('===============================\n')
                run_water_tap(m=m, objective=False, skip_small=skip_small_sens)
                print(scenario, stash_value[q] * i, 'LCOW -->', m.fs.costing.LCOW())

                lcow_list.append(value(m.fs.costing.LCOW))
                water_recovery_list.append(value(m.fs.costing.system_recovery))
                scenario_value.append(sum(stash_value) * i)
                scenario_name.append(scenario)
                elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
                elec_int.append(value(m.fs.costing.electricity_intensity))
                baseline_sens_value.append(sum(stash_value))
                baseline_lcows.append(baseline_lcow)
                baseline_elect_ints.append(baseline_elect_int)
                lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
                lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
                sens_vars.append(sens_var)
                treated_water.append(value(m.fs.costing.treated_water))
                treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
                elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
                sens_var_norm.append(i)
                ro_pressure.append(None)
                ro_press_norm.append(None)
                ro_area.append(None)
                ro_area_norm.append(None)
                mem_replacement.append(None)


            for q, key in enumerate(m.fs.flow_in_dict):
                getattr(m.fs, key).flow_vol_in[0].fix(stash_value[q])

    ############################################################
    print('\n-------', 'RESET', '-------\n')
    run_water_tap(m=m, objective=False, skip_small=True)
    print('LCOW -->', m.fs.costing.LCOW())
    ############ lifetime years ############

    stash_value = value(m.fs.costing_param.plant_lifetime_yrs)
    scenario = 'Plant Lifetime 15-45 yrs'
    sens_var = 'plant_life'
    print('-------', scenario, '-------')
    ub = 45
    lb = 15
    step = (ub - lb) / runs_per_scenario
    for i in np.arange(lb, ub + step, step):
        m.fs.costing_param.plant_lifetime_yrs = i
        print('\n===============================')
        print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
        print('===============================\n')
        run_water_tap(m=m, objective=False, skip_small=True)
        print(scenario, i, 'LCOW -->', m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))
        baseline_sens_value.append(stash_value)
        baseline_lcows.append(baseline_lcow)
        baseline_elect_ints.append(baseline_elect_int)
        lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
        lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
        sens_vars.append(sens_var)
        treated_water.append(value(m.fs.costing.treated_water))
        treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
        elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
        sens_var_norm.append(i - stash_value)
        ro_pressure.append(None)
        ro_press_norm.append(None)
        ro_area.append(None)
        ro_area_norm.append(None)
        mem_replacement.append(None)

    m.fs.costing_param.plant_lifetime_yrs = stash_value
    ############################################################
    print('\n-------', 'RESET', '-------\n')
    run_water_tap(m=m, objective=False, skip_small=True)
    print('LCOW -->', m.fs.costing.LCOW())
    ############ elec cost +-30% ############

    stash_value = value(m.fs.costing_param.electricity_price)
    scenario = 'Electricity Price +- 30%'
    sens_var = 'elect_price'
    print('-------', scenario, '-------')
    ub = stash_value * 1.3
    lb = stash_value * 0.7
    step = (ub - lb) / runs_per_scenario
    for i in np.arange(lb, ub + step, step):
        m.fs.costing_param.electricity_price = i
        print('\n===============================')
        print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
        print('===============================\n')
        run_water_tap(m=m, objective=False, skip_small=True)
        print(scenario, i * stash_value, 'LCOW -->', m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i * stash_value)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))
        baseline_sens_value.append(stash_value)
        baseline_lcows.append(baseline_lcow)
        baseline_elect_ints.append(baseline_elect_int)
        lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
        lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
        sens_vars.append(sens_var)
        treated_water.append(value(m.fs.costing.treated_water))
        treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
        elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
        sens_var_norm.append(i / stash_value)
        ro_pressure.append(None)
        ro_press_norm.append(None)
        ro_area.append(None)
        ro_area_norm.append(None)
        mem_replacement.append(None)

    m.fs.costing_param.electricity_price = stash_value

    ############################################################
    print('\n-------', 'RESET', '-------\n')
    run_water_tap(m=m, objective=False, skip_small=True)
    print('LCOW -->', m.fs.costing.LCOW())

    # dwi_list = ['emwd', 'big_spring', 'kbhdp']
    # if m.fs.train['case_study'] in dwi_list:
    for key in m.fs.pfd_dict.keys():
        if m.fs.pfd_dict[key]['Unit'] == 'deep_well_injection':

            stash_value = value(getattr(m.fs, key).lift_height[0])
            scenario = 'Injection Pressure LH 100-2000 ft'
            sens_var = 'dwi_inj_pressure'
            print('-------', scenario, '-------')
            ub = 3500
            lb = 100
            step = (ub - lb) / runs_per_scenario
            for i in np.arange(lb, ub + step, step):
                getattr(m.fs, key).lift_height.fix(i)
                print('\n===============================')
                print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
                print('===============================\n')
                run_water_tap(m=m, objective=False, skip_small=True)
                print(scenario, i, 'LCOW -->', m.fs.costing.LCOW())

                lcow_list.append(value(m.fs.costing.LCOW))
                water_recovery_list.append(value(m.fs.costing.system_recovery))
                scenario_value.append(i)
                scenario_name.append(scenario)
                elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
                elec_int.append(value(m.fs.costing.electricity_intensity))
                baseline_sens_value.append(stash_value)
                baseline_lcows.append(baseline_lcow)
                baseline_elect_ints.append(baseline_elect_int)
                lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
                lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
                sens_vars.append(sens_var)
                treated_water.append(value(m.fs.costing.treated_water))
                treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
                elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
                sens_var_norm.append(i / stash_value)
                ro_pressure.append(None)
                ro_press_norm.append(None)
                ro_area.append(None)
                ro_area_norm.append(None)
                mem_replacement.append(None)

            getattr(m.fs, key).lift_height.fix(stash_value)

    ############################################################

    ############################################################
    print('\n-------', 'RESET', '-------\n')
    run_water_tap(m=m, objective=False, skip_small=True)
    print('LCOW -->', m.fs.costing.LCOW())
    ############ power sens -> adjust recovery of pre-evap pond to see evaporation area needs ############

    # cherokee
    # set RO recovery for ccro + brine to change, evap pond area unfixed and calculated by model, recovery set at 90%.
    # same for gila baseline

    m.fs.area_list = area_list = []

    # if m.fs.train['case_study'] == "cherokee" and m_scenario == "zld_ct":
    #     if 'reverse_osmosis_a' in m.fs.pfd_dict.keys():
    #         stash_value = value(getattr(m.fs, 'evaporation_pond').area[0])
    #         cenario = 'Area'
    #         sens_var = 'evap_pond_area'
    #         print('-------', scenario, '-------')
    #
    #         lb = 0.45
    #         ub = 0.95
    #         step = (ub - lb) / 50  # 50 runs
    #         getattr(m.fs, 'evaporation_pond').water_recovery.fix(0.9)
    #         getattr(m.fs, 'evaporation_pond').area.unfix()
    #
    #
    #         for recovery_rate in np.arange(lb, ub + step, step):
    #             m.fs.reverse_osmosis_a.kurby4 = Constraint(
    #                     expr=m.fs.reverse_osmosis_a.flow_vol_out[0] >=
    #                          (recovery_rate * m.fs.reverse_osmosis_a.flow_vol_in[0]))
    #             print('\n===============================')
    #             print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
    #             print('===============================\n')
    #             run_water_tap(m=m, objective=False, skip_small=True)
    #             print(scenario, recovery_rate, 'LCOW -->', m.fs.costing.LCOW())
    #
    #             lcow_list.append(value(m.fs.costing.LCOW))
    #             water_recovery_list.append(value(m.fs.costing.system_recovery))
    #             scenario_value.append(recovery_rate)
    #             scenario_name.append(scenario)
    #             elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
    #             elec_int.append(value(m.fs.costing.electricity_intensity))
    #             area_list.append(value(m.fs.evaporation_pond.area[0]))
    #
    #         getattr(m.fs, key).water_recovery.unfix()
    #         getattr(m.fs, key).area.fix(stash_value)
    #         df_area = pd.DataFrame(area_list)
    #         df_area.to_csv('results/case_studies/area_list_%s_%s_%s.csv' % (
    #                 m.fs.train['case_study'], m_scenario, key))

    #         for key in m.fs.pfd_dict.keys():
    #             if m.fs.pfd_dict[key]['Unit'] == 'evaporation_pond':

    #                 stash_value = value(getattr(m.fs, key).area[0])
    #                 scenario = 'Area'
    #                 sens_var = 'evap_pond_area'
    #                 print('-------', scenario, '-------')
    #                 if m.fs.train['case_study'] == 'cherokee':
    #                     ub = 1.5
    #                     lb = 0.75
    #                 if m.fs.train['case_study'] == 'gila_river':
    #                     lb = 0.5
    #                     ub = 1.05
    #                 step = (ub - lb) / 50  # 50 runs
    #                 for i in np.arange(lb, ub + step, step):
    #                     getattr(m.fs, key).area.fix(i * stash_value)
    #                     getattr(m.fs, key).water_recovery.unfix()
    #                     run_water_tap(m=m, objective=False, skip_small=True)
    #                     print(scenario, i * stash_value, 'LCOW -->', m.fs.costing.LCOW())

    #                     lcow_list.append(value(m.fs.costing.LCOW))
    #                     water_recovery_list.append(value(m.fs.costing.system_recovery))
    #                     scenario_value.append(i * stash_value)
    #                     scenario_name.append(scenario)
    #                     elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
    #                     elec_int.append(value(m.fs.costing.electricity_intensity))
    #                     area_list.append(value(m.fs.evaporation_pond.area[0]))

    #                 getattr(m.fs, key).area.fix(stash_value)
    #                 df_area = pd.DataFrame(area_list)
    #                 df_area.to_csv('results/case_studies/area_list_%s_%s_%s.csv' % (
    #                         m.fs.train['case_study'], m_scenario, key))

    ############################################################
    print('\n-------', 'RESET', '-------\n')
    run_water_tap(m=m, objective=False, skip_small=True)
    print('LCOW -->', m.fs.costing.LCOW())
    ############ RO scenarios --> pressure % change, membrane area, replacement rate% ############

    if m_scenario not in ['edr_ph_ro', 'ro_and_mf']:
        if m.fs.train['case_study'] in ['cherokee', 'gila_river', 'upw']:
            print('skips RO sens')
        else:
            for key in m.fs.pfd_dict.keys():
                if m.fs.pfd_dict[key]['Unit'] == 'reverse_osmosis':
                    if key in ro_list:
                        # if m.fs.train['case_study'] == 'ocwd':
                        #     m.fs.del_component(m.fs.ro_pressure_constr)
                        area = value(getattr(m.fs, key).membrane_area[0])
                        scenario_dict = {
                                'membrane_area': [-area * 0.2, area * 0.2],
                                'pressure': [0.85, 1.15],
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
                                print('\n===============================')
                                print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
                                print('===============================\n')
                                run_water_tap(m=m, objective=False, skip_small=skip_small_sens)
                                print(scenario, i, 'LCOW -->', m.fs.costing.LCOW())

                                lcow_list.append(value(m.fs.costing.LCOW))
                                water_recovery_list.append(value(m.fs.costing.system_recovery))
                                scenario_value.append(i)
                                scenario_name.append(key + '_' + scenario)
                                elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
                                elec_int.append(value(m.fs.costing.electricity_intensity))
                                baseline_sens_value.append(stash_value)
                                baseline_lcows.append(baseline_lcow)
                                baseline_elect_ints.append(baseline_elect_int)
                                lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
                                lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
                                sens_vars.append(key + '_' + scenario)
                                treated_water.append(value(m.fs.costing.treated_water))
                                treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
                                elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
                                sens_var_norm.append(i / stash_value)
                                ro_pressure.append(value(getattr(getattr(getattr(m.fs, key), 'feed'), 'pressure')[0]))
                                ro_area.append(value(getattr(getattr(m.fs, key), 'membrane_area')[0]))
                                mem_replacement.append(value(getattr(getattr(m.fs, key), 'factor_membrane_replacement')[0]))
                                if scenario == 'pressure':
                                    ro_press_norm.append(ro_pressure[-1] / stash_value)
                                    ro_area_norm.append(None)
                                elif scenario == 'membrane_area':
                                    ro_area_norm.append(ro_area[-1] / stash_value)
                                    ro_press_norm.append(None)
                                elif scenario == 'factor_membrane_replacement':
                                    ro_area_norm.append(None)
                                    ro_press_norm.append(None)

                            if scenario == 'pressure':
                                getattr(getattr(getattr(m.fs, key), 'feed'), scenario).fix(stash_value)
                            else:
                                getattr(getattr(m.fs, key), scenario).fix(stash_value)

    ############################################################
    # in depth sens analysis #
    # if m.fs.train['case_study'] in ['san_luis']:
    #
    #     tds_in = False
    #
    #     for key in m.fs.flow_in_dict:
    #         if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
    #             tds_in = True
    #
    #     if tds_in is True:
    #         print('\n-------', 'RESET', '-------\n')
    #         run_water_tap(m=m, objective=False, skip_small=True)
    #         print('LCOW -->', m.fs.costing.LCOW())
    #
    #         ############ salinity  +-30% ############
    #         stash_value = []
    #         for key in m.fs.flow_in_dict:
    #             if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
    #                 stash_value.append(value(getattr(m.fs, key).conc_mass_in[0, 'tds']))
    #         print(stash_value)
    #         scenario = 'Inlet TDS +-25%'
    #         print('-------', scenario, '-------')
    #         ub = 1.25
    #         lb = 0.75
    #
    #         step = (ub - lb) / 1000
    #
    #         for i in np.arange(lb, ub + step, step):
    #             q = 0
    #             for key in m.fs.flow_in_dict:
    #                 if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
    #                     getattr(m.fs, key).conc_mass_in[0, 'tds'].fix(stash_value[q] * i)
    #                     q += 1
    #             print('\n===============================')
    #             print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
    #             print('===============================\n')
    #             run_water_tap(m=m, objective=False, skip_small=skip_small_sens)
    #             print(scenario, sum(stash_value) * i, 'LCOW -->', m.fs.costing.LCOW())
    #
    #             lcow_list.append(value(m.fs.costing.LCOW))
    #             water_recovery_list.append(value(m.fs.costing.system_recovery))
    #             scenario_value.append(sum(stash_value) * i)
    #             scenario_name.append(scenario)
    #             elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
    #             elec_int.append(value(m.fs.costing.electricity_intensity))
    #
    #         q = 0
    #         for key in m.fs.flow_in_dict:
    #             if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
    #                 getattr(m.fs, key).conc_mass_in[0, 'tds'].fix(stash_value[q])
    #                 q += 1

    ############################################################
    ############################################################
    ############################################################
    ############################################################

    # toc_in = False
    # for key in m.fs.flow_in_dict:
    #     if 'toc' in list(getattr(m.fs, key).config.property_package.component_list):
    #         toc_in = True
    #
    # if toc_in:
    #     print('\n-------', 'RESET', '-------\n')
    #     run_water_tap(m=m, objective=False, skip_small=True)
    #     print('LCOW -->', m.fs.costing.LCOW())
    #
    #     ############ TOC  +-30% ############
    #     stash_value = []
    #     for key in m.fs.flow_in_dict:
    #         if 'toc' in list(getattr(m.fs, key).config.property_package.component_list):
    #             stash_value.append(value(getattr(m.fs, key).conc_mass_in[0, 'toc']))
    #     print(stash_value)
    #     scenario = 'Inlet TOC +-25%'
    #     sens_var = 'toc_in'
    #     print('-------', scenario, '-------')
    #     ub = 1.25
    #     lb = 0.75
    #
    #     step = (ub - lb) / runs_per_scenario
    #
    #     for i in np.arange(lb, ub + step, step):
    #         q = 0
    #         for key in m.fs.flow_in_dict:
    #             if 'toc' in list(getattr(m.fs, key).config.property_package.component_list):
    #                 getattr(m.fs, key).conc_mass_in[0, 'toc'].fix(stash_value[q] * i)
    #                 q += 1
    #         print('\n===============================')
    #         print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
    #         print('===============================\n')
    #         run_water_tap(m=m, objective=False, skip_small=skip_small_sens)
    #         print(scenario, sum(stash_value) * i, 'LCOW -->', m.fs.costing.LCOW())
    #
    #         lcow_list.append(value(m.fs.costing.LCOW))
    #         water_recovery_list.append(value(m.fs.costing.system_recovery))
    #         scenario_value.append(sum(stash_value) * i)
    #         scenario_name.append(scenario)
    #         elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
    #         elec_int.append(value(m.fs.costing.electricity_intensity))
    #         baseline_sens_value.append(stash_value)
    #         baseline_lcows.append(baseline_lcow)
    #         baseline_elect_ints.append(baseline_elect_int)
    #         lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
    #         lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
    #         sens_vars.append(sens_var)
    #         treated_water.append(value(m.fs.costing.treated_water))
    #         treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
    #         elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
    #         sens_var_norm.append(i / stash_value)
    #
    #
    #     q = 0
    #     for key in m.fs.flow_in_dict:
    #         if 'toc' in list(getattr(m.fs, key).config.property_package.component_list):
    #             getattr(m.fs, key).conc_mass_in[0, 'toc'].fix(stash_value[q])
    #             q += 1

    print('\n-------', 'RESET', '-------\n')
    run_water_tap(m=m, objective=False, skip_small=True)
    print('LCOW -->', m.fs.costing.LCOW())

    ############ Component Replacement Costs -75% ############
    stash_value = m.fs.costing_param.maintenance_costs_percent_FCI()

    print(stash_value)
    scenario = 'Component Replacement Costs -75%'
    sens_var = 'component_replacement'
    print('-------', scenario, '-------')
    ub = 1
    lb = 0.1

    step = (ub - lb) / runs_per_scenario

    for i in np.arange(lb, ub + step, step):
        m.fs.costing_param.maintenance_costs_percent_FCI.fix(stash_value * i)
        print('\n===============================')
        print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
        print('===============================\n')
        run_water_tap(m=m, objective=False, skip_small=skip_small_sens)
        print(scenario, stash_value * i, 'LCOW -->', m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(stash_value * i)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))
        baseline_sens_value.append(stash_value)
        baseline_lcows.append(baseline_lcow)
        baseline_elect_ints.append(baseline_elect_int)
        lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
        lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
        sens_vars.append(sens_var)
        treated_water.append(value(m.fs.costing.treated_water))
        treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
        elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
        sens_var_norm.append((stash_value * i) / stash_value)
        ro_pressure.append(None)
        ro_press_norm.append(None)
        ro_area.append(None)
        ro_area_norm.append(None)
        mem_replacement.append(None)

    ############################################################
    ############################################################
    ############################################################
    ############################################################

    if m.fs.train['case_study'] in ['monterey_one']:
        stash_value = m.fs.coag_and_floc.alum_dose[0]()
        print(stash_value)
        scenario = 'Alum Dose 0.5-20 mg/L'
        sens_var = 'alum_dose'
        print('-------', scenario, '-------')
        ub = 0.020
        lb = 0.0005
        step = (ub - lb) / runs_per_scenario
        for i in np.arange(lb, ub + step, step):
            m.fs.coag_and_floc.alum_dose.fix(i)
            print('\n===============================')
            print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}\n')
            print('===============================\n')
            run_water_tap(m=m, objective=False, skip_small=True)
            print(scenario, i, 'LCOW -->', m.fs.costing.LCOW())

            lcow_list.append(value(m.fs.costing.LCOW))
            water_recovery_list.append(value(m.fs.costing.system_recovery))
            scenario_value.append(i)
            scenario_name.append(scenario)
            elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
            elec_int.append(value(m.fs.costing.electricity_intensity))
            baseline_sens_value.append(value(stash_value))
            baseline_lcows.append(baseline_lcow)
            baseline_elect_ints.append(baseline_elect_int)
            lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
            lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
            sens_vars.append(sens_var)
            treated_water.append(value(m.fs.costing.treated_water))
            treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
            elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
            sens_var_norm.append(value(i / stash_value))
            ro_pressure.append(None)
            ro_press_norm.append(None)
            ro_area.append(None)
            ro_area_norm.append(None)
            mem_replacement.append(None)

        m.fs.coag_and_floc.alum_dose.fix(stash_value)

    ############################################################

    # final run to get baseline numbers again
    run_water_tap(m=m, objective=True, skip_small=skip_small_sens)

    sens_df['sensitivity_var'] = sens_vars
    sens_df['baseline_sens_value'] = baseline_sens_value
    sens_df['scenario_value'] = scenario_value
    sens_df['sensitivity_var_norm'] = sens_var_norm
    sens_df['lcow'] = lcow_list
    sens_df['lcow_norm'] = lcow_norm
    sens_df['lcow_diff'] = lcow_diff
    sens_df['baseline_lcow'] = baseline_lcows
    sens_df['water_recovery'] = water_recovery_list
    sens_df['treated_water_vol'] = treated_water
    sens_df['baseline_treated_water'] = baseline_treated_water
    sens_df['treated_water_norm'] = treated_water_norm
    sens_df['elec_lcow'] = elec_lcow
    sens_df['baseline_elect_int'] = baseline_elect_ints
    sens_df['elec_int'] = elec_int
    sens_df['elect_int_norm'] = elect_int_norm
    sens_df['scenario_name'] = scenario_name
    sens_df['lcow_difference'] = sens_df.lcow - value(m.fs.costing.LCOW)
    sens_df['water_recovery_difference'] = (sens_df.water_recovery - value(m.fs.costing.system_recovery))
    sens_df['elec_lcow_difference'] = (sens_df.elec_lcow - value(m.fs.costing.elec_frac_LCOW))
    sens_df.elec_lcow = sens_df.elec_lcow * 100
    sens_df.water_recovery = sens_df.water_recovery * 100
    sens_df['ro_pressure'] = ro_pressure
    sens_df['ro_press_norm'] = ro_press_norm
    sens_df['ro_area'] = ro_area
    sens_df['ro_area_norm'] = ro_area_norm
    sens_df['mem_replacement'] = mem_replacement



    if save_results:
        sens_df.to_csv('results/case_studies/%s_%s_sensitivity.csv' % (case_study, m_scenario), index=False)
    if return_results:
        return sens_df

    print('\n====================== END SENSITIVITY ANALYSIS ======================\n')


def print_ro_results(m):
    pressures = []
    recovs = []
    areas = []
    num_mems = []
    kws = []
    kss = []
    fluxs = []
    flow_ins = []
    flow_outs = []

    object_dict = dict()
    pfd_dict = m.fs.pfd_dict
    for i, unit in enumerate(m.fs.component_objects(Block, descend_into=False)):
        if i == 0:
            print('\n===========================RO RESULTS=================================\n')
        unit_name = str(unit)[3:]
        print_name = unit_name.replace('_', ' ').title().replace('Ro', 'RO')
        if unit_name in pfd_dict.keys() and pfd_dict[unit_name]['Unit'] == 'reverse_osmosis':
            pressures.append(unit.feed.pressure[0]())
            recovs.append(unit.ro_recovery())
            areas.append(unit.membrane_area[0]())
            num_mems.append(unit.num_membranes())
            kws.append(unit.a[0]())
            kss.append(unit.b[0]())
            fluxs.append(unit.flux_lmh)
            flow_ins.append(unit.flow_vol_in[0]())
            flow_outs.append(unit.flow_vol_out[0]())
            print(f'.. {print_name}:')
            print(f'\tPressure = {round(pressures[-1], 2)} bar = {round(pressures[-1] * 14.5038)} psi')
            print(f'\tRecovery = {round(recovs[-1], 3) * 100}%')
            print(f'\tArea = {round(areas[-1])} m2 ---> {round(num_mems[-1])} membrane modules')
            print(f'\tFlux = {round(value(fluxs[-1]), 1)} LMH')
            print(f'\tFeed Flow Rate = {round(unit.flow_vol_in[0](), 5)} m3/s = {round(pyunits.convert(unit.flow_vol_in[0], to_units=pyunits.Mgallons / pyunits.day)(), 5)} MGD')
            print(f'\tPermeate Flow Rate= {round(unit.flow_vol_out[0](), 5)} m3/s = {round(pyunits.convert(unit.flow_vol_out[0], to_units=pyunits.Mgallons / pyunits.day)(), 5)} MGD')
            print(f'\tReject Flow Rate= {round(unit.flow_vol_waste[0](), 5)} m3/s = {round(pyunits.convert(unit.flow_vol_waste[0], to_units=pyunits.Mgallon / pyunits.day)(), 5)} MGD')
            print(f'\tWater Perm. = {kws[-1]} m/(bar.hr)')
            print(f'\tSalt Perm. = {kss[-1]} m/hr\n')

    # if len(pressures) > 1:
    #     sys_flux = sum(flow_outs) / sum(areas) * (pyunits.meter / pyunits.sec)
    #     sys_flux = pyunits.convert(sys_flux, to_units=(pyunits.liter / pyunits.m ** 2 / pyunits.hour))
    #     avg_press = sum(pressures) / len(pressures)
    #
    #     print(f'.. System:')
    #     print(f'\tPressure (avg.)= {round(avg_press, 2)} bar = {round(avg_press * 14.5)} psi')
    #     print(f'\tRecovery = {round(sum(flow_outs) / sum(flow_ins), 3) * 100}%')
    #     print(f'\tArea = {round(sum(areas))} m2 ---> {round(sum(num_mems))} membrane modules')
    #     print(f'\tFlux = {round(sys_flux(), 1)} LMH')
    #     print(f'\tWater Perm. = {kws[-1]} m/(bar.hr)')
    #     print(f'\tSalt Perm. = {kss[-1]} m/hr')


def print_ro_bounds(source_water_category, feed_flux_min, feed_flux_max, min_pressure, max_pressure,
                    min_area, a=None, b=None):
    if source_water_category == 'seawater':
        print(f'\n\nSEAWATER for RO:'
              f'\n\tFlux [LMH] (min, max) = {feed_flux_min, feed_flux_max}'
              f'\n\tPressure [bar] (min, max) = {min_pressure, max_pressure}'
              f'\n\tMin. Area [m2] = {min_area}'
              )
    else:
        print(f'\n\nOTHER bounds for RO:'
              f'\n\tFlux [LMH] (min, max) = {feed_flux_min, feed_flux_max}'
              f'\n\tPressure [bar] (min, max) = {min_pressure, max_pressure}'
              f'\n\tMin. Area [m2] = {min_area}'
              )


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

    q = 1
    for key in m.fs.pfd_dict.keys():
        if m.fs.pfd_dict[key]['Unit'] == 'reverse_osmosis':

            setattr(m, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).pure_water_flux[0] * 3600 <= feed_flux_max))
            q += 1
            setattr(m, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).pure_water_flux[0] * 3600 >= feed_flux_min))
            q += 1
            setattr(m, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).membrane_area[0] >= min_area))
            q += 1
            setattr(m, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).feed.pressure[0] <= max_pressure))
            q += 1
            setattr(m.fs, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).a[0] <= a[1]))
            q += 1
            setattr(m.fs, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).a[0] >= a[0]))
            setattr(m.fs, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).b[0] <= b[1]))
            q += 1
            setattr(m.fs, ('flux_constraint%s' % q), Constraint(
                    expr=getattr(m.fs, key).b[0] >= b[0]))
            q += 1

    run_water_tap(m=m, objective=True, skip_small=True)


    return m


def case_study_constraints(m, case_study, scenario):
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
            m.fs.reverse_osmosis.kurby1 = Constraint(expr=m.fs.reverse_osmosis.flow_vol_out[0] <= (0.75 * m.fs.reverse_osmosis.flow_vol_in[0]) * 1.01)
            m.fs.reverse_osmosis.kurby2 = Constraint(expr=m.fs.reverse_osmosis.flow_vol_out[0] >= (0.75 * m.fs.reverse_osmosis.flow_vol_in[0]) * 0.99)

        if 'reverse_osmosis_a' in m.fs.pfd_dict.keys():
            m.fs.reverse_osmosis_a.kurby4 = Constraint(expr=m.fs.reverse_osmosis_a.flow_vol_out[0] >= (0.95 * m.fs.reverse_osmosis_a.flow_vol_in[0]))

    if case_study == 'san_luis':
        if scenario in ['baseline', 'dwi']:
            m.fs.reverse_osmosis_1.feed.pressure.fix(25.5)
            m.fs.reverse_osmosis_2.feed.pressure.fix(36)


    if case_study == 'kbhdp':
        m.fs.ro_recovery_constr1 = Constraint(expr=(m.fs.ro_first_stage.flow_vol_out[0] + m.fs.ro_second_stage.flow_vol_out[0]) / m.fs.ro_first_stage.flow_vol_in[0] <= 0.83)
        m.fs.ro_recovery_constr2 = Constraint(expr=(m.fs.ro_first_stage.flow_vol_out[0] + m.fs.ro_second_stage.flow_vol_out[0]) / m.fs.ro_first_stage.flow_vol_in[0] >= 0.81)
        m.fs.ro1_press_constr2 = Constraint(expr=m.fs.ro_first_stage.feed.pressure[0] <= 14)
        m.fs.ro2_press_constr2 = Constraint(expr=m.fs.ro_second_stage.feed.pressure[0] <= 18)
        m.fs.ro_area_constr1 = Constraint(expr=m.fs.ro_first_stage.membrane_area[0] / m.fs.ro_second_stage.membrane_area[0] <= 2.1)
        m.fs.ro_area_constr2 = Constraint(expr=m.fs.ro_first_stage.membrane_area[0] / m.fs.ro_second_stage.membrane_area[0] >= 1.9)  # m.fs.ro_first_stage.a.unfix()  # m.fs.ro_second_stage.a.unfix()  # m.fs.ro_first_stage.b.unfix()  # m.fs.ro_second_stage.b.unfix()

    if case_study == 'emwd':
        if scenario in ['baseline', 'dwi']:
            m.fs.manifee_area_constr = Constraint(expr=m.fs.ro_a1.membrane_area[0] == m.fs.ro_a2.membrane_area[0])
            m.fs.perris_area_constr = Constraint(expr=m.fs.ro_b1.membrane_area[0] == m.fs.ro_b2.membrane_area[0])
            m.fs.manifee_pressure_constr1 = Constraint(expr=m.fs.ro_a1.feed.pressure[0] <= 14)
            m.fs.manifee_pressure_constr2 = Constraint(expr=m.fs.ro_a1.feed.pressure[0] == m.fs.ro_a2.feed.pressure[0])
            m.fs.perris_pressure_constr1 = Constraint(expr=m.fs.ro_b1.feed.pressure[0] <= 14)
            m.fs.perris_pressure_constr2 = Constraint(expr=m.fs.ro_b1.feed.pressure[0] == m.fs.ro_b2.feed.pressure[0])
            m.fs.area_constr1 = Constraint(expr=(m.fs.ro_b1.membrane_area[0] + m.fs.ro_b2.membrane_area[0]) / (m.fs.ro_a1.membrane_area[0] + m.fs.ro_a2.membrane_area[0]) >= 1.4)
            m.fs.area_constr2 = Constraint(expr=(m.fs.ro_b1.membrane_area[0] + m.fs.ro_b2.membrane_area[0]) / (m.fs.ro_a1.membrane_area[0] + m.fs.ro_a2.membrane_area[0]) <= 1.6)

        elif 'zld' in scenario:
            m.fs.ro1_press_constr1 = Constraint(expr=m.fs.ro_a_first_pass.feed.pressure[0] <= 14)
            m.fs.ro1_press_constr2 = Constraint(expr=m.fs.ro_a_first_pass.feed.pressure[0] == m.fs.ro_b_first_pass.feed.pressure[0])
            m.fs.ro2_press_constr1 = Constraint(expr=m.fs.ro_a_second_pass.feed.pressure[0] <= 18)
            m.fs.ro2_press_constr2 = Constraint(expr=m.fs.ro_a_second_pass.feed.pressure[0] == m.fs.ro_b_second_pass.feed.pressure[0])
            m.fs.area_constr1 = Constraint(expr=(m.fs.ro_b_first_pass.membrane_area[0] + m.fs.ro_b_second_pass.membrane_area[0]) / (m.fs.ro_a_first_pass.membrane_area[0] + m.fs.ro_a_second_pass.membrane_area[0]) >= 1.4)
            m.fs.area_constr2 = Constraint(expr=(m.fs.ro_b_first_pass.membrane_area[0] + m.fs.ro_b_second_pass.membrane_area[0]) / (m.fs.ro_a_first_pass.membrane_area[0] + m.fs.ro_a_second_pass.membrane_area[0]) <= 1.6)
            m.fs.ro_area_constr1 = Constraint(expr=m.fs.ro_a_first_pass.membrane_area[0] <= m.fs.ro_a_second_pass.membrane_area[0])
            m.fs.ro_area_constr2 = Constraint(expr=m.fs.ro_b_first_pass.membrane_area[0] <= m.fs.ro_b_second_pass.membrane_area[0])
            m.fs.area_ratio_constr1 = Constraint(expr=(m.fs.ro_a_first_pass.membrane_area[0] / m.fs.ro_a_second_pass.membrane_area[0]) == (m.fs.ro_b_first_pass.membrane_area[0] / m.fs.ro_b_second_pass.membrane_area[0]))

    if case_study == 'ocwd':  # Facility data in email from Dan Giammar 7/7/2021
        m.fs.ro_pressure_constr = Constraint(expr=m.fs.reverse_osmosis.feed.pressure[0] <= 15)  # Facility data: RO pressure is 140-220 psi (~9.7-15.1 bar)
        m.fs.microfiltration.water_recovery.fix(0.9)

    if case_study == 'produced_water_injection' and scenario == 'swd_well':
        m.fs.brine_concentrator.water_recovery.fix(0.725)

    if case_study == "uranium":
        m.fs.ion_exchange.removal_fraction[0, "tds"].unfix()
        m.fs.ion_exchange.water_recovery.fix(0.967)
        m.fs.ion_exchange.anion_res_capacity.unfix()
        m.fs.ion_exchange.cation_res_capacity.unfix()

    return m


def find_arcs_and_ports(m, unit, get_ports=False, keep_inlet=False, keep_outlet=False):

    def delete_arcs(arcs):
        for arc in arcs:
            try:
                deleted_arcs.append(arc)
                m.fs.del_component(arc)
            except:
                continue

    m.fs.deleted_arcs = deleted_arcs = []
    unit_inlets = []
    unit_outlets = []
    for component in unit.component_objects():
        if type(component) == SimplePort:
            component_str = str(component).split('.')[-1]
            arcs = component.arcs()
            if 'inlet' in component_str and keep_inlet:
                unit_inlets.append(component)
                for arc in arcs:
                    print('keep', str(unit), component_str, str(arc))
                continue
            elif 'outlet' in component_str and keep_outlet:
                unit_outlets.append(component)
                for arc in arcs:
                    print('keep', str(unit), component_str, str(arc))
                continue
            elif 'inlet' in component_str:
                unit_inlets.append(component)
                for arc in arcs:
                    print('delete', str(unit), component_str, str(arc))
                    delete_arcs(arcs)
            elif 'outlet' in component_str:
                unit_outlets.append(component)
                for arc in arcs:
                    print('delete', str(unit), component_str, str(arc))
                    delete_arcs(arcs)
    if get_ports:
        return unit_inlets, unit_outlets
    else:
        return


def set_new_arcs(m, from_unit_dict, to_unit_dict):
    outlets = from_unit_dict['outlets']
    inlets = to_unit_dict['inlets']
    if len(outlets) != len(inlets):
        print('there must be an equal number of inlets and outlets!')
        return
#     for i, port in enumerate(outlets, 1):
    arc_name = from_unit_dict['name'].split('_')[0] + '_to_' + to_unit_dict['name'].split('_')[0] + '_arc'
    print(arc_name)
    setattr(m.fs, arc_name, Arc(source=outlets[0], destination=inlets[0]))
    return m


def make_decision(m, case_study, scenario):

    def connected_units(u, units=[]):
        if isinstance(u, list):
            for unit in u:
                next_unit = temp_pfd_dict[unit]['ToUnitName']
                if next_unit in units:
                    continue
                units.append(next_unit)
                connected_units(next_unit, units=units)
            return units
        if u is np.nan:
            return units
        next_unit = temp_pfd_dict[u]['ToUnitName']
        if next_unit is np.nan:
            return units
        if isinstance(next_unit, list):
            for unit in next_unit:
                if unit in units:
                    continue
                units.append(unit)
                connected_units(unit, units=units)
            return units
        else:
            if next_unit in units:
                return units
            units.append(next_unit)
            connected_units(next_unit, units=units)
            return units

    m.fs.units_to_drop = units_to_drop = []
    m.fs.units_to_keep = units_to_keep = []

    for splitter_num, destination_dict in m.fs.unit_options.items():
        splitter_name = 'splitter' + str(splitter_num)
        splitter = getattr(m.fs, splitter_name)
        m.fs.from_unit_name = from_unit_name = list(destination_dict.keys())[0]
        temp_unit_names = [d.replace('_', ' ').title() for d in destination_dict[from_unit_name]]
        print(f'For {splitter_name.title()} from {from_unit_name.title()} to {*temp_unit_names, }:')
        from_unit = getattr(m.fs, from_unit_name)
        from_unit_flow_out = from_unit.flow_vol_out[0]()
        decision_dict = {}
        m.fs.decision_vars = decision_vars = []
        m.fs.decision_vals = decision_vals = []
        m.fs.dest_units = dest_units = []
        m.fs.drop_decision_units = drop_decision_units = []
        outlets = []
        m.fs.split_fraction_vars = split_fraction_vars = []
        m.fs.from_unit_dict = from_unit_dict = {}
        m.fs.to_unit_dict = to_unit_dict = {}
        m.fs.deleted_units = deleted_units = []
    #     num_decision_var = len(destinations)
        for i, destination in enumerate(destination_dict[from_unit_name], 1):
            decision_var_name = 'decision_var_outlet' + str(i)
            outlet_name = 'flow_vol_outlet' + str(i)
            split_fraction_var_name = 'split_fraction_outlet' + str(i)
            split_fraction_var = getattr(splitter, split_fraction_var_name)
            split_fraction_vars.append(split_fraction_var)
            decision_var = getattr(splitter, decision_var_name)
            outlet = getattr(splitter, outlet_name)
            outlets.append(outlet)
            decision_vars.append(decision_var)
            decision_vals.append(decision_var[0]())
            dest_unit = getattr(m.fs, destination)
            dest_units.append(dest_unit)
            temp_name = destination.replace('_', ' ').title()
            print(f'\tFlow weight to {temp_name} = {round(decision_vals[-1], 3)}')

        max_index = decision_vals.index(max(decision_vals))


        for i, v in enumerate(decision_vars):
            if i != max_index:
                # v.fix(0)
                # split_fraction_vars[i].fix(0)
                drop_decision_units.append(dest_units[i].unit_name)
                del_index = m.fs.df_units[m.fs.df_units['UnitName'] == drop_decision_units[-1]].index
                m.fs.df_units.drop(del_index, inplace=True)
            else:
                # v.fix(1)
                # split_fraction_vars[i].fix(1)
                continue

        # decision_vars[max_index].fix(1)
        # split_fraction_vars[max_index].fix(1)
        # split_fraction_vars[min_index].fix(0)
        # m.fs.del_component(splitter.split_fraction_constr)
        # outlets[max_index].fix(from_unit_flow_out)
        # decision_vars[min_index].fix(0)
        # m.fs.del_unit_name = del_unit_name = dest_units[min_index].unit_name
        m.fs.to_unit_name = to_unit_name = dest_units[max_index].unit_name
        temp_name = to_unit_name.replace('_', ' ').title()
        print(f'\tWT3 directs flow to {temp_name}\n')

        df_from_unit = m.fs.df_units.set_index('UnitName').loc[from_unit_name]
        from_unit_params = ast.literal_eval(df_from_unit.Parameter)
        new_params = str()
        for param in from_unit_params.items():
            if 'split_fraction' in param:
                continue
            new_params += "'" + param[0] + "'" + ':' + str(param[1])

        new_params = '{' + new_params + '}'
        df_from_unit.Parameter = new_params
        df_from_unit.ToUnitName = to_unit_name
        df_from_unit.FromPort = 'outlet'
        df_from_unit['UnitName'] = from_unit_name

        from_index = m.fs.df_units[m.fs.df_units['UnitName'] == from_unit_name].index
        m.fs.df_units.drop(from_index, inplace=True)

        m.fs.df_units.loc[from_index[0]] = df_from_unit

        m.fs.temp_pfd_dict = temp_pfd_dict = get_pfd_dict(m.fs.df_units)

        for drop in drop_decision_units:
            m.fs.start_u = start_u = m.fs.pfd_dict[drop]['ToUnitName']
            if isinstance(start_u, list):
                temp_drop = connected_units(start_u, units=[s for s in start_u])
            else:
                temp_drop = connected_units(start_u, units=[start_u])
            units_to_drop += temp_drop

        temp_keep = connected_units(from_unit_name, units=[])
        units_to_keep += temp_keep

    units_to_drop = list(set(units_to_drop))
    units_to_keep = list(set(units_to_keep))

    for u in units_to_keep:
        if u in units_to_drop:
            idx = units_to_drop.index(u)
            units_to_drop.pop(idx)

    for u in units_to_drop:
        remove_idx = m.fs.df_units[m.fs.df_units.UnitName == u].index
        m.fs.df_units.drop(remove_idx, inplace=True)

    m.fs.df_units.sort_index(inplace=True)
    m.fs.new_df_units = new_df_units = m.fs.df_units.copy()

    m = watertap_setup(case_study=case_study, scenario=scenario)
    m = get_case_study(m=m, new_df_units=new_df_units)

    return m


        # m.fs.del_component(splitter)
        # find_arcs_and_ports(m, splitter)
        # deleted_units.append(splitter)

        # m.fs.del_component(del_unit)
        # find_arcs_and_ports(m, del_unit)
        # deleted_units.append(del_unit)

        # to_unit_inlets, to_unit_outlets = find_arcs_and_ports(m, to_unit, get_ports=True, keep_outlet=True)
        # from_unit_inlets, from_unit_outlets = find_arcs_and_ports(m, from_unit, get_ports=True, keep_inlet=True)
        #
        # from_unit_dict['name'] = from_unit.unit_name
        # to_unit_dict['name'] = to_unit.unit_name
        # from_unit_dict['inlets'] = from_unit_inlets
        # to_unit_dict['inlets'] = to_unit_inlets
        # from_unit_dict['outlets'] = from_unit_outlets
        # to_unit_dict['outlets'] = to_unit_outlets

        # m = set_new_arcs(m, from_unit_dict, to_unit_dict)

    # return m


def check_has_ro(m):
    has_ro = False
    for key in m.fs.pfd_dict.keys():
        if m.fs.pfd_dict[key]['Unit'] == 'reverse_osmosis':
            getattr(m.fs, key).feed.pressure.unfix()
            getattr(m.fs, key).membrane_area.unfix()
            has_ro = True
    if has_ro:
        return True
    else:
        return False


def run_water_tap_ro(m, return_df=False, skip_small=True,
                     desired_recovery=1, ro_bounds='seawater', source_scenario=None, scenario_name=None):
    scenario = scenario_name
    case_study = m.fs.train['case_study']
    reference = m.fs.train['reference']
    case_study_print = case_study.replace('_', ' ').swapcase()
    scenario_print = scenario.replace('_', ' ').swapcase()
    time = m.fs.config.time
    print(f'===================================\nCase Study = {case_study_print}\nScenario = '
          f'{scenario_print}\n===================================')

    run_water_tap(m=m, objective=True, skip_small=skip_small)

    if m.fs.choose:
        m = make_decision(m, case_study, scenario)
        financials.get_system_costing(m.fs)
        run_water_tap(m=m, objective=True, skip_small=skip_small)
        m = case_study_constraints(m, case_study, scenario)
        has_ro = check_has_ro(m)
        if has_ro:
            m = set_bounds(m, source_water_category=ro_bounds)

    else:
        m = case_study_constraints(m, case_study, scenario)
        has_ro = check_has_ro(m)
        if has_ro:
            m = set_bounds(m, source_water_category=ro_bounds)

    if desired_recovery < 1:
        if m.fs.costing.system_recovery() > desired_recovery:
            print('Running for desired recovery -->', desired_recovery)
            m.fs.recovery_bound = Constraint(expr=m.fs.costing.system_recovery <= desired_recovery)
            m.fs.recovery_bound1 = Constraint(expr=m.fs.costing.system_recovery >= desired_recovery - 1.5)

            if scenario_name == 'baseline':
                run_water_tap(m=m, objective=True, skip_small=skip_small)
            else:
                run_water_tap(m=m, objective=True, skip_small=skip_small, print_model_results='summary')

        else:
            print('System recovery already lower than desired recovery.'
                  '\n\tDesired:', desired_recovery, '\n\tCurrent:', m.fs.costing.system_recovery())


    ######## UNCOMMENT HERE AND BELOW TO RUN REST OF MODEL ############

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

    if scenario == 'edr_ph_ro':
        m.fs.primary_separator.conc_mass_in[0, 'tds'].fix(7)
        m.fs.primary_separator.conc_mass_in[0, 'boron'].fix(0.03)

    if scenario == 'ro_and_mf':
        m.fs.primary_separator.conc_mass_in[0, 'tds'].fix(10)

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
        if m.fs.new_case_study:
            new_df_units = m.fs.df_units.copy()
            m = watertap_setup(dynamic=False, case_study=case_study, reference=reference, scenario=scenario, source_scenario=source_scenario)
            m = get_case_study(m=m, new_df_units=new_df_units)

        else:
            m = watertap_setup(dynamic=False, case_study=case_study, reference=reference, scenario=scenario, source_scenario=source_scenario)
            m = get_case_study(m=m)

        has_ro = check_has_ro(m)

        for key in m.fs.pfd_dict.keys():
            unit = str(key).replace('_', ' ').swapcase()
            if m.fs.pfd_dict[key]['Unit'] == 'reverse_osmosis':
                getattr(m.fs, key).feed.pressure.unfix()
                getattr(m.fs, key).membrane_area.unfix()

        if case_study == 'upw':
            m.fs.media_filtration.water_recovery.fix(0.9)
            m.fs.splitter2.split_fraction_outlet3.fix(upw_list[0])
            m.fs.splitter2.split_fraction_outlet4.fix(upw_list[1])

        if case_study == 'ocwd':  # Facility data in email from Dan Giammar 7/7/2021
            # m.fs.ro_pressure_constr = Constraint(expr=m.fs.reverse_osmosis.feed.pressure[0] <= 15)  # Facility data: RO pressure is 140-220 psi (~9.7-15.1 bar)
            m.fs.microfiltration.water_recovery.fix(0.9)

        if case_study == 'uranium':
            m.fs.ion_exchange.removal_fraction[0, 'tds'].fix(ur_list[0])
            m.fs.ion_exchange.anion_res_capacity.fix(ur_list[1])
            m.fs.ion_exchange.cation_res_capacity.fix(ur_list[2])

        run_water_tap(m=m, objective=True, skip_small=skip_small)

        m.fs.objective_function.deactivate()

        for key in m.fs.pfd_dict.keys():
            if m.fs.pfd_dict[key]['Unit'] == 'reverse_osmosis':
                getattr(m.fs, key).feed.pressure.fix(ro_stash[key]['feed.pressure'])
                getattr(m.fs, key).membrane_area.fix(ro_stash[key]['membrane_area'])
                getattr(m.fs, key).a.fix(ro_stash[key]['a'])
                getattr(m.fs, key).b.fix(ro_stash[key]['b'])

    run_water_tap(m=m, objective=False, print_model_results='summary', skip_small=True)

    if has_ro:
        print_ro_results(m)

    df = get_results_table(m=m, case_study=case_study, scenario=scenario_name)

    if return_df:
        return m, df
    else:
        return m