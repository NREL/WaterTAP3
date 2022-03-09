import ast
import logging
from re import template
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
import pyomo.environ
from pyomo.gdp import *

warnings.filterwarnings('ignore')

__all__ = ['watertap_setup', 'run_model', 'run_and_return_model', 'run_model_no_print', 
            'run_watertap3', 'case_study_constraints', 'get_ix_stash', 'fix_ix_stash',
            'print_ro_results', 'print_results', 'set_bounds', 'get_ro_stash', 'fix_ro_stash', 
            'make_decision', 'connected_units']


def watertap_setup(dynamic=False, case_study=None, reference='nawi', scenario=None,
                   source_reference=None, source_case_study=None, source_scenario=None, new_df_units=None):

    '''
    Initial setup of WaterTAP3 model. 

    Create flowsheet and read in basic information about model (water sources, units in treatment train)
    '''

    def get_source(reference, water_type, case_study, scenario):
        '''
        Read in water source data. 
        '''
        input_file = 'data/case_study_water_sources.csv'
        df = pd.read_csv(input_file, index_col='variable')
        try:
            source_df = df[((df.case_study == case_study) & (df.water_type == water_type) & (df.reference == reference) & (df.scenario == scenario))].copy()
            source_flow = source_df.loc['flow'].value
        except:
            source_df = df[((df.case_study == case_study) & (df.water_type == water_type) & (df.reference == reference) & (df.scenario == 'baseline'))].copy()
            source_flow = source_df.loc['flow'].value
        source_df.drop(source_df[source_df.index == 'flow'].index, inplace=True)
        return source_flow, source_df

    case_study_print = case_study.replace('_', ' ').swapcase()
    scenario_print = scenario.replace('_', ' ').swapcase()

    m_name = f'{case_study_print}: {scenario_print}'
    m = ConcreteModel(name=m_name)

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

    df = pd.read_csv('data/treatment_train_setup.csv') # Read in treatment train input sheet.

    water_type_list = []
    if new_df_units is not None:
        m.fs.df_units = new_df_units.copy()
    else:
        m.fs.df_units = df[((df.Reference == reference) & (df.Scenario == scenario) & (df.CaseStudy == case_study))].copy()
        print(f'\nCase Study = {case_study_print}'
              f'\nScenario = {scenario_print}\n')

    m.fs.has_ro = False
    m.fs.has_ix = False
    if 'ion_exchange' in m.fs.df_units.Unit:
        m.fs.has_ix = True
    if 'reverse_osmosis' in m.fs.df_units.Unit:
        m.fs.has_ro = True

    for i in m.fs.df_units[m.fs.df_units.Type == 'intake'].index:
        temp_dict = ast.literal_eval(m.fs.df_units[m.fs.df_units.Type == 'intake'].loc[i]['Parameter'])
        for water_type in temp_dict['water_type']:
            water_type_list.append(water_type)

    if len(water_type_list) == 1:
        water_type_list = water_type_list[0]

    m.fs.source_water = {
            'case_study': source_case_study,
            'reference': source_reference,
            'scenario': source_scenario,
            'water_type': water_type_list
            }

    flow_dict = {}

    if isinstance(m.fs.source_water['water_type'], list):
        m.fs.source_df = pd.DataFrame()
        for water_type in m.fs.source_water['water_type']:
            source_flow, source_df = get_source(m.fs.source_water['reference'],
                                                water_type,
                                                m.fs.source_water['case_study'],
                                                m.fs.source_water['scenario'])
            flow_dict[water_type] = source_flow
            m.fs.source_df = m.fs.source_df.append(source_df)


    else:
        source_flow, source_df = get_source(m.fs.source_water['reference'],
                                            m.fs.source_water['water_type'],
                                            m.fs.source_water['case_study'],
                                            m.fs.source_water['scenario'])
        flow_dict[m.fs.source_water['water_type']] = source_flow
        m.fs.source_df = source_df

    m.fs.flow_in_dict = flow_dict

    return m


def run_and_return_model(m, solver='ipopt', tolerance=None, tee=False, objective=False, 
                        max_attempts=3, print_it=False, initial_run=True, mip_solver='glpk'):

    '''
    Function to attempt model solve and return model object.
    '''

    if initial_run:
        financials.get_system_costing(m.fs)

    TransformationFactory('network.expand_arcs').apply_to(m)

    if objective:
        m.fs.objective_function = Objective(expr=m.fs.costing.LCOW)

    model_solver = SolverFactory(solver)
    if tolerance and solver == 'ipopt':
        model_solver.options['tol'] = tolerance

    logging.getLogger('pyomo.core').setLevel(logging.ERROR)

    print('.................................')
    print('\nDegrees of Freedom:', degrees_of_freedom(m))
    if solver == 'gdpopt':
        m.fs.results = results = model_solver.solve(m, tee=tee, mip_solver=mip_solver)
    else:
        m.fs.results = results = model_solver.solve(m, tee=tee)
    
    print(f'\nInitial solve attempt {results.solver.termination_condition.swapcase()}')

    attempt_number = 1
    while ((m.fs.results.solver.termination_condition in ['infeasible', 'maxIterations', 'unbounded', 'other']) & (attempt_number <= max_attempts)):
        print(f'\nAttempt {attempt_number}:')
        if solver == 'gdpopt':
            m.fs.results = results = model_solver.solve(m, tee=tee, mip_solver=mip_solver)
        else:
            m.fs.results = results = model_solver.solve(m, tee=tee)
        print(f'\n\tWaterTAP3 solver returned {results.solver.termination_condition.swapcase()} solution...')
        attempt_number += 1

    print(f'\nWaterTAP3 solution {results.solver.termination_condition.swapcase()}\n')
    print('.................................')

    if print_it:
        print_results(m)

    return m

def run_model(m, solver='ipopt', tolerance=None, tee=False, objective=False, 
                max_attempts=3, print_it=False, initial_run=True, mip_solver='glpk'):
    
    '''
    Function used to attempt model solve.
    '''

    if initial_run:
        financials.get_system_costing(m.fs)

    TransformationFactory('network.expand_arcs').apply_to(m)

    if objective:
        m.fs.objective_function = Objective(expr=m.fs.costing.LCOW)

    model_solver = SolverFactory(solver)
    if tolerance and solver == 'ipopt':
        model_solver.options['tol'] = tolerance

    logging.getLogger('pyomo.core').setLevel(logging.ERROR)

    print('.................................')
    print('\nDegrees of Freedom:', degrees_of_freedom(m))
    if solver == 'gdpopt':
        m.fs.results = results = model_solver.solve(m, tee=tee, mip_solver=mip_solver)
    else:
        m.fs.results = results = model_solver.solve(m, tee=tee)
    print(f'\nInitial solve attempt {results.solver.termination_condition.swapcase()}')

    attempt_number = 1
    while ((m.fs.results.solver.termination_condition in ['infeasible', 'maxIterations', 'unbounded', 'other']) & (attempt_number <= max_attempts)):
        print(f'\nAttempt {attempt_number}:')
        if solver == 'gdpopt':
            m.fs.results = results = model_solver.solve(m, tee=tee, mip_solver=mip_solver)
        else:
            m.fs.results = results = model_solver.solve(m, tee=tee)
        print(f'\n\tWaterTAP3 solver returned {results.solver.termination_condition.swapcase()} solution...')
        attempt_number += 1

    print(f'\nWaterTAP3 solution {results.solver.termination_condition.swapcase()}\n')
    print('.................................')

    if print_it:
        print_results(m)

def run_model_no_print(m, solver='ipopt', tolerance=None, tee=False, objective=False, 
                        max_attempts=3, initial_run=True, mip_solver='glpk'):

    if initial_run:
        financials.get_system_costing(m.fs)

    TransformationFactory('network.expand_arcs').apply_to(m)

    if objective:
        m.fs.objective_function = Objective(expr=m.fs.costing.LCOW)

    model_solver = SolverFactory(solver)
    if tolerance and solver == 'ipopt':
        model_solver.options['tol'] = tolerance
    # m.fs.solver = solver = SolverFactory('glpk')

    logging.getLogger('pyomo.core').setLevel(logging.ERROR)

    if solver == 'gdpopt':
        m.fs.results = results = model_solver.solve(m, tee=tee, mip_solver=mip_solver)
    else:
        m.fs.results = results = model_solver.solve(m, tee=tee)

    attempt_number = 1
    while ((m.fs.results.solver.termination_condition in ['infeasible', 'maxIterations', 'unbounded']) & (attempt_number <= max_attempts)):
        if solver == 'gdpopt':
            m.fs.results = results = model_solver.solve(m, tee=tee, mip_solver=mip_solver)
        else:
            m.fs.results = results = model_solver.solve(m, tee=tee)
        attempt_number += 1

def run_watertap3(m, desired_recovery=1, ro_bounds='seawater', solver='ipopt', 
                    return_df=False, tolerance=None, tee=False):
    
    '''
    Function to run WaterTAP3
    '''

    print('\n=========================START WT3 MODEL RUN==========================')
    scenario = m.fs.train['scenario']
    case_study = m.fs.train['case_study']
    reference = m.fs.train['reference']

    run_model(m, solver=solver, objective=True, tolerance=tolerance, tee=tee)

    if m.fs.results.solver.termination_condition != 'optimal':
        raise Exception(f'\n\tMODEL RUN ABORTED:'
              f'\n\tWT3 solution is {m.fs.results.solver.termination_condition.swapcase()}'
              f'\n\tModel did not solve optimally after 3 attempts. No results are saved.'
              f'\n\tCheck model setup and initial conditions and retry.')

    if m.fs.choose:
        print(f'********TREATMENT TRAIN CONTAINS DECISION VARIABLE********')
        print('Removing non-optimal unit processes...\n\n')
        m = make_decision(m, case_study, scenario)
        print('The following units were dropped:')
        for dropped_unit in m.fs.all_dropped_units:
            print(f"\t{dropped_unit.replace('_', ' ').swapcase()}")
        print('\n=======================OPTIMIZED TREATMENT TRAIN=======================')
        run_model(m, solver=solver, objective=True, tolerance=tolerance, tee=tee)
        if m.fs.results.solver.termination_condition != 'optimal':
            raise Exception(f'\n\tMODEL RUN ABORTED:'
              f'\n\tWT3 solution is {m.fs.results.solver.termination_condition.swapcase()}'
              f'\n\tModel did not solve optimally after 3 attempts. No results are saved.'
              f'\n\tCheck model setup and initial conditions and retry.')

    if m.fs.has_ix:
        m, ix_stash = get_ix_stash(m)
        print('Initial IX solve OK...\nFixing number IX columns...')
        # m = fix_ix_stash(m, ix_stash, only_num_cols=True)
        m = fix_ix_stash(m, ix_stash)
        run_model(m, solver=solver, objective=True, tolerance=tolerance)
        # if m.fs.results.solver.termination_condition != 'optimal':
        #     raise Exception(f'\n\tMODEL RUN ABORTED:'
        #         f'\n\tWT3 solution is {m.fs.results.solver.termination_condition.swapcase()}'
        #         f'\n\tIX did not solve after fixing the number of columns.')
                 
        # print('IX solved!\nFixing other IX variables...')
        # m, ix_stash = get_ix_stash(m)
        # m = fix_ix_stash(m, ix_stash)


    m = case_study_constraints(m, case_study, scenario)

    if m.fs.has_ro:
        if case_study == 'upw':
            m.fs.splitter2.split_fraction_constr = Constraint(expr=sum(m.fs.splitter2.split_fraction_vars) <= 1.001)
            m.fs.splitter2.split_fraction_constr2 = Constraint(expr=sum(m.fs.splitter2.split_fraction_vars) >= 0.999)
        m = set_bounds(m, source_water_category=ro_bounds)
        if m.fs.results.solver.termination_condition != 'optimal':
            print(f'\n\tMODEL RUN ABORTED AFTER SETTING RO BOUNDS:'
                  f'\n\tWT3 solution is {m.fs.results.solver.termination_condition.swapcase()}'
                  f'\n\tModel did not solve optimally after 3 attempts. No results are saved.'
                  f'\n\tCheck model setup and initial conditions and retry.')
            return m

    if desired_recovery < 1:
        if m.fs.costing.system_recovery() > desired_recovery:
            print('Running for desired recovery -->', desired_recovery)
            m.fs.recovery_bound = Constraint(expr=m.fs.costing.system_recovery <= desired_recovery)
            m.fs.recovery_bound1 = Constraint(expr=m.fs.costing.system_recovery >= desired_recovery - 1.5)

            run_model(m, objective=True, tolerance=tolerance)
            if m.fs.results.solver.termination_condition != 'optimal':
                print(f'\n\tMODEL RUN ABORTED WHILE TARGETING SYSTEM RECOVERY OF {desired_recovery * 100}:'
                      f'\n\tWT3 solution is {m.fs.results.solver.termination_condition.swapcase()}'
                      f'\n\tModel did not solve optimally after 3 attempts. No results are saved.'
                      f'\n\tCheck model setup and initial conditions and retry.')
                return m
        else:
            print('System recovery already lower than desired recovery.'
                  '\n\tDesired:', desired_recovery, '\n\tCurrent:', m.fs.costing.system_recovery())

    if case_study == 'uranium':
        ur_list = []
        ur_list.append(m.fs.ion_exchange.removal_fraction[0, 'tds']())
        ur_list.append(m.fs.ion_exchange.anion_res_capacity[0]())
        ur_list.append(m.fs.ion_exchange.cation_res_capacity[0]())

    # change this to set splitters
    if case_study == 'upw':
        m.fs.upw_list = upw_list = []
        upw_list.append(m.fs.splitter2.split_fraction_outlet_1[0]())
        upw_list.append(m.fs.splitter2.split_fraction_outlet_2[0]())

    if m.fs.has_ro:
        m, ro_stash = get_ro_stash(m)
        ###### RESET BOUNDS AND DOUBLE CHECK RUN IS OK SO CAN GO INTO SENSITIVITY #####
        if m.fs.new_case_study:
            new_df_units = m.fs.df_units.copy()
            all_dropped_units = m.fs.all_dropped_units
            m = watertap_setup(dynamic=False, case_study=case_study, scenario=scenario, new_df_units=new_df_units)
            m.fs.all_dropped_units = all_dropped_units
            m = get_case_study(m=m, new_df_units=new_df_units)
            # if m.fs.has_ix:
            #     m = fix_ix_stash(m, ix_stash)

        else:
            m = watertap_setup(dynamic=False, case_study=case_study, scenario=scenario)
            m = get_case_study(m=m)
            # if m.fs.has_ix:
            #     m = fix_ix_stash(m, ix_stash)

        if case_study == 'gila_river' and scenario != 'baseline':
            m.fs.evaporation_pond.water_recovery.fix(0.895)

        if case_study == 'upw':
            run_model(m, solver=solver, objective=True, tolerance=tolerance)
            m.fs.upw_list = upw_list
            m.fs.media_filtration.water_recovery.fix(0.9)
            m.fs.splitter2.split_fraction_outlet_1.fix(upw_list[0])
            m.fs.splitter2.split_fraction_outlet_2.fix(upw_list[1])

        if case_study == 'ocwd':  # Facility data in email from Dan Giammar 7/7/2021
            # m.fs.ro_pressure_constr = Constraint(expr=m.fs.reverse_osmosis.feed.pressure[0] <= 15)  # Facility data: RO pressure is 140-220 psi (~9.7-15.1 bar)
            m.fs.microfiltration.water_recovery.fix(0.9)

        if case_study == 'uranium':
            m.fs.ion_exchange.removal_fraction[0, 'tds'].fix(ur_list[0])
            m.fs.ion_exchange.anion_res_capacity.fix(ur_list[1])
            m.fs.ion_exchange.cation_res_capacity.fix(ur_list[2])

        if case_study == 'irwin':
            run_model(m, solver=solver, objective=True, tolerance=tolerance)
            m.fs.brine_concentrator.water_recovery.fix(0.8)
        
        run_model(m, solver=solver, objective=True, tolerance=tolerance)
        m = fix_ro_stash(m, ro_stash)
        m.fs.objective_function.deactivate()
        # m = fix_ro_stash(m, ro_stash)
        if m.fs.has_ix:
        #     m, ix_stash = get_ix_stash(m)
            m = fix_ix_stash(m, ix_stash)

    run_model(m, solver=solver, objective=False, print_it=True, tolerance=tolerance)

    if m.fs.results.solver.termination_condition != 'optimal':
        print(f'\nFINAL MODEL RUN ABORTED:'
              f'\n\tWT3 solution is {m.fs.results.solver.termination_condition.swapcase()}'
              f'\n\tModel did not solve optimally after 3 attempts. No results are saved.'
              f'\n\tCheck model setup and initial conditions and retry.')
        return m

    m, df = get_results_table(m=m, case_study=case_study, scenario=scenario)

    print('\n==========================END WT3 MODEL RUN===========================')

    if return_df:
        return m, df
    else:
        return m


def get_ix_stash(m):
    m.fs.ix_stash = ix_stash = {}
    df = m.fs.df_units.set_index(['UnitName'])
    for u in df.index:
        unit_module = df.loc[u].Unit
        if unit_module == 'ion_exchange':
            unit = getattr(m.fs, u)
            ix_stash[u] = {
                        'sfr': unit.sfr(),
                        'resin_depth': unit.resin_depth(),
                        'column_diam': unit.column_diam(),
                        'num_columns': unit.num_columns()
                        }

    return m, ix_stash


def fix_ix_stash(m, ix_stash, only_num_cols=False):
    if only_num_cols:
        for ix in ix_stash.keys():
            unit = getattr(m.fs, ix)
            unit.num_columns.fix(ix_stash[ix]['num_columns'])
        return m
    else:
        for ix in ix_stash.keys():
            unit = getattr(m.fs, ix)
            unit.sfr.fix(ix_stash[ix]['sfr'])
            # unit.num_columns.fix(ix_stash[ix]['num_columns'])
            unit.resin_depth.fix(ix_stash[ix]['resin_depth'])
            # unit.column_diam.fix(ix_stash[ix]['column_diam'])

        return m


def get_ro_stash(m):
    m.fs.ro_stash = ro_stash = {}
    for k, v in m.fs.pfd_dict.items():
        if v['Unit'] == 'reverse_osmosis':
            unit = getattr(m.fs, k)
            ro_stash[k] = {
                    'feed.pressure': unit.feed.pressure[0](),
                    'membrane_area': unit.membrane_area[0](),
                    'a': unit.a[0](),
                    'b': unit.b[0]()
                    }
    return m, ro_stash


def fix_ro_stash(m, ro_stash):
    for ro in ro_stash.keys():
        unit = getattr(m.fs, ro)
        unit.feed.pressure.fix(ro_stash[ro]['feed.pressure'])
        unit.membrane_area.fix(ro_stash[ro]['membrane_area'])
        unit.a.fix(ro_stash[ro]['a'])
        unit.b.fix(ro_stash[ro]['b'])

    return m


def print_results(m):
    case_study = m.fs.train['case_study']
    scenario = m.fs.train['scenario']
    case_study_print = case_study.replace('_', ' ').swapcase()
    scenario_print = scenario.replace('_', ' ').swapcase()
    print(f'\n{case_study_print}: {scenario_print}')
    print('=========================SYSTEM LEVEL RESULTS=========================')
    print('LCOW ($/m3):', round(value(m.fs.costing.LCOW()), 5))
    print('Total Capital Investment ($MM):', round(value(m.fs.costing.capital_investment_total()), 3))
    print('Total Annual Operating Costs ($MM/yr):', round(value(m.fs.costing.operating_cost_annual()), 3))
    print('Annual Fixed Operating Cost ($MM/yr):', round(value(m.fs.costing.fixed_op_cost_annual()), 3))
    print('Annual Catalysts and Chemicals Cost ($MM/yr):', round(value(m.fs.costing.cat_and_chem_cost_annual()), 3))
    print('Annual Electricity Costs ($MM/yr):', round(value(m.fs.costing.electricity_cost_annual()), 3))
    print('Annual Other Variable Costs ($MM/yr):', round(value(m.fs.costing.other_var_cost_annual()), 3))
    print('Treated water (m3/s):', round(value(m.fs.costing.treated_water()), 3))
    print('Total water recovery (%):', round(value(100 * m.fs.costing.system_recovery()), 3))
    print('Electricity intensity (kWh/m3):', round(value(m.fs.costing.electricity_intensity()), 3))
    print('Electricity portion of LCOW (%):', round(value(100 * m.fs.costing.elec_frac_LCOW()), 3))
    print('======================================================================')
    print('\n=========================UNIT PROCESS RESULTS=========================\n')
    for unit in m.fs.df_units.UnitName:
        b_unit = getattr(m.fs, unit)
        print(f'\n{b_unit.unit_pretty_name}:')
        print('\tTotal Capital Investment ($MM):', round(value(b_unit.costing.total_cap_investment()), 5))
        print('\tAnnual O&M ($MM/yr):', round(value(b_unit.costing.annual_op_main_cost), 5))
        print('\tAnnual Fixed O&M ($MM/yr):', round(value(b_unit.costing.total_fixed_op_cost), 5))
        print('\tAnnual Chemical Cost ($MM/yr):', round(value(b_unit.costing.cat_and_chem_cost), 5))
        print('\tAnnual Electricity Cost ($MM/yr):', round(value(b_unit.costing.electricity_cost), 5))
        print('\tElectricity Intensity (kWh/m3):', round(value(b_unit.costing.electricity_intensity()), 5))
        print('\tUnit LCOW ($/m3):', round(value(b_unit.LCOW()), 5))
        print('\tFlow In (m3/s):', round(value(b_unit.flow_vol_in[0]()), 5))
        print('\tFlow Out (m3/s):', round(value(b_unit.flow_vol_out[0]()), 5))
        print('\tFlow Waste (m3/s):', round(value(b_unit.flow_vol_waste[0]()), 5))
        if b_unit.unit_type == 'reverse_osmosis':
            print_ro_results(m, b_unit.unit_name)
        if b_unit.unit_type in ['brine_concentrator', 'evaporation_pond', 'landfill', 'landfill_zld']:
            try:
                print('\tTDS in (mg/L):', round(value(b_unit.conc_mass_in[0, 'tds']) * 1000, 1))
                print('\tTDS out (mg/L):', round(value(b_unit.conc_mass_out[0, 'tds']) * 1000, 1))
                print('\tTDS waste (mg/L):', round(value(b_unit.conc_mass_waste[0, 'tds']) * 1000, 1))
            except:
                print(f'\tNO TDS INTO {b_unit.unit_pretty_name}')
            if b_unit.unit_type == 'evaporation_pond':
                print(f'\tPond Area (acres): {round(b_unit.area[0](), 3)}')
            print('\tWater Recovery (%):', round(value((b_unit.flow_vol_out[0]() / b_unit.flow_vol_in[0]())), 5) * 100)
        elif b_unit.unit_type != 'reverse_osmosis':
            print('\tWater Recovery (%):', round(value(b_unit.water_recovery[0]()), 5) * 100)

    print('\n======================================================================\n')


def print_ro_results(m, ro_name):
    pressures = []
    recovs = []
    areas = []
    num_mems = []
    kws = []
    kss = []
    fluxs = []
    flow_ins = []
    flow_outs = []
    tds_in = []
    tds_out = []
    tds_waste = []

    # for i, u in enumerate(m.fs.df_units.Unit):
    #     if u == 'reverse_osmosis':
    # ro_name = m.fs.df_units.iloc[i].UnitName
    unit = getattr(m.fs, ro_name)
    pressures.append(unit.feed.pressure[0]())
    recovs.append(unit.ro_recovery())
    areas.append(unit.membrane_area[0]())
    num_mems.append(unit.num_membranes())
    kws.append(unit.a[0]())
    kss.append(unit.b[0]())
    fluxs.append(unit.flux_lmh)
    flow_ins.append(unit.flow_vol_in[0]())
    flow_outs.append(unit.flow_vol_out[0]())
    tds_in.append(unit.conc_mass_in[0, 'tds']())
    tds_out.append(unit.conc_mass_out[0, 'tds']())
    tds_waste.append(unit.conc_mass_waste[0, 'tds']())
    # print(f'.. {print_name}:')
    print(f'\n\t.....{unit.unit_pretty_name} OPERATIONAL PARAMETERS.....')
    print(f'\tPressure = {round(pressures[-1], 2)} bar = {round(pressures[-1] * 14.5038)} psi')
    print(f'\tArea = {round(areas[-1])} m2 ---> {round(num_mems[-1])} membrane modules')
    print(f'\tFlux = {round(value(fluxs[-1]), 1)} LMH')
    print(f'\tTDS in = {round(value(tds_in[-1]) * 1000, 3)} mg/L')
    print(f'\tTDS out = {round(value(tds_out[-1]) * 1000, 3)} mg/L')
    print(f'\tTDS waste = {round(value(tds_waste[-1]) * 1000, 3)} mg/L')
    print(f'\tFlow in = {round(unit.flow_vol_in[0](), 5)} m3/s = '
          f'{round(pyunits.convert(unit.flow_vol_in[0], to_units=pyunits.Mgallons / pyunits.day)(), 5)} MGD = '
          f'{round(pyunits.convert(unit.flow_vol_in[0], to_units=pyunits.gallons / pyunits.min)(), 2)} gpm')
    print(f'\tFlow out = {round(unit.flow_vol_out[0](), 5)} m3/s = '
          f'{round(pyunits.convert(unit.flow_vol_out[0], to_units=pyunits.Mgallons / pyunits.day)(), 5)} MGD = '
          f'{round(pyunits.convert(unit.flow_vol_out[0], to_units=pyunits.gallons / pyunits.min)(), 2)} gpm')
    print(f'\tFlow waste = {round(unit.flow_vol_waste[0](), 5)} m3/s = '
          f'{round(pyunits.convert(unit.flow_vol_waste[0], to_units=pyunits.Mgallon / pyunits.day)(), 5)} MGD = '
          f'{round(pyunits.convert(unit.flow_vol_waste[0], to_units=pyunits.gallons / pyunits.min)(), 2)} gpm')
    print(f'\tWater Permeability = {kws[-1]} m/(bar.hr)')
    print(f'\tSalt Permeability = {kss[-1]} m/hr')
    print(f'\tRO Recovery = {round(recovs[-1], 3) * 100}%')

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

    run_model(m=m, objective=True)

    return m


def case_study_constraints(m, case_study, scenario):
    if case_study == 'upw':
        m.fs.media_filtration.water_recovery.fix(0.9)
        m.fs.reverse_osmosis.eq1_upw = Constraint(expr=m.fs.reverse_osmosis.flow_vol_out[0] <= 0.05678 * 1.01)
        m.fs.reverse_osmosis.eq2_upw = Constraint(expr=m.fs.reverse_osmosis.flow_vol_out[0] >= 0.05678 * 0.99)
        m.fs.reverse_osmosis.eq3_upw = Constraint(expr=m.fs.reverse_osmosis.flow_vol_waste[0] <= 0.04416 * 1.01)
        m.fs.reverse_osmosis.eq4_upw = Constraint(expr=m.fs.reverse_osmosis.flow_vol_waste[0] >= 0.04416 * 0.99)
        m.fs.reverse_osmosis_2.eq1 = Constraint(expr=m.fs.reverse_osmosis_2.flow_vol_out[0] <= 0.01262 * 1.01)
        m.fs.reverse_osmosis_2.eq2 = Constraint(expr=m.fs.reverse_osmosis_2.flow_vol_out[0] >= 0.01262 * 0.99)
        m.fs.ro_stage.eq1_upw = Constraint(expr=m.fs.ro_stage.flow_vol_out[0] <= 0.03154 * 1.01)
        m.fs.ro_stage.eq2_upw = Constraint(expr=m.fs.ro_stage.flow_vol_out[0] >= 0.03154 * 0.99)
    #
        if scenario not in ['baseline']:
            m.fs.to_zld_constr1 = Constraint(expr=m.fs.to_zld.flow_vol_in[0] >= 0.99 * 0.0378)
            m.fs.to_zld_constr2 = Constraint(expr=m.fs.to_zld.flow_vol_in[0] <= 1.01 * 0.0378)

    if case_study == 'uranium':
        m.fs.ro_production.eq1_anna = Constraint(expr=m.fs.ro_production.flow_vol_out[0] <= (0.7 * m.fs.ro_production.flow_vol_in[0]) * 1.01)
        m.fs.ro_production.eq2_anna = Constraint(expr=m.fs.ro_production.flow_vol_out[0] >= (0.7 * m.fs.ro_production.flow_vol_in[0]) * 0.99)
        m.fs.ro_restore_stage.eq3_anna = Constraint(expr=m.fs.ro_restore_stage.flow_vol_out[0] <= (0.5 * m.fs.ro_restore_stage.flow_vol_in[0]) * 1.01)
        m.fs.ro_restore_stage.eq4_anna = Constraint(expr=m.fs.ro_restore_stage.flow_vol_out[0] >= (0.5 * m.fs.ro_restore_stage.flow_vol_in[0]) * 0.99)
        m.fs.ro_restore.eq5_anna = Constraint(expr=m.fs.ro_restore.flow_vol_out[0] <= (0.75 * m.fs.ro_restore.flow_vol_in[0]) * 1.01)
        m.fs.ro_restore.eq6_anna = Constraint(expr=m.fs.ro_restore.flow_vol_out[0] >= (0.75 * m.fs.ro_restore.flow_vol_in[0]) * 0.99)

    if case_study == 'gila_river':
        if 'reverse_osmosis' in m.fs.pfd_dict.keys():
            m.fs.reverse_osmosis.recov1 = Constraint(expr=m.fs.reverse_osmosis.flow_vol_out[0] <= (0.59 * m.fs.reverse_osmosis.flow_vol_in[0]) * 1.01)
            m.fs.reverse_osmosis.recov2 = Constraint(expr=m.fs.reverse_osmosis.flow_vol_out[0] >= (0.59 * m.fs.reverse_osmosis.flow_vol_in[0]) * 0.99)

        if scenario != 'baseline':
            m.fs.evaporation_pond.water_recovery.fix(0.895)

    if case_study == 'cherokee':

        if 'boiler_ro' in m.fs.pfd_dict.keys():
            m.fs.boiler_ro.recov1 = Constraint(expr=m.fs.boiler_ro.flow_vol_out[0] <= (0.75 * m.fs.boiler_ro.flow_vol_in[0]) * 1.01)
            m.fs.boiler_ro.recov2 = Constraint(expr=m.fs.boiler_ro.flow_vol_out[0] >= (0.75 * m.fs.boiler_ro.flow_vol_in[0]) * 0.99)

        if 'reverse_osmosis_a' in m.fs.pfd_dict.keys():
            m.fs.reverse_osmosis_a.recov1 = Constraint(expr=m.fs.reverse_osmosis_a.flow_vol_out[0] >= (0.95 * m.fs.reverse_osmosis_a.flow_vol_in[0]))

    if case_study == 'san_luis':
        if scenario in ['baseline', 'dwi', '1p5_mgd', '3_mgd', '5_mgd']:
            m.fs.reverse_osmosis_1.feed.pressure.fix(25.5)
            m.fs.reverse_osmosis_2.feed.pressure.fix(36)

        # if '1p5' in scenario:
        #     m.fs.irrigation_and_drainage.flow_vol_in.fix(0.0657)

    if case_study == 'kbhdp':
        m.fs.ro_recovery_constr1 = Constraint(expr=(m.fs.ro_first_stage.flow_vol_out[0] + m.fs.ro_second_stage.flow_vol_out[0]) / m.fs.ro_first_stage.flow_vol_in[0] <= 0.83)
        m.fs.ro_recovery_constr2 = Constraint(expr=(m.fs.ro_first_stage.flow_vol_out[0] + m.fs.ro_second_stage.flow_vol_out[0]) / m.fs.ro_first_stage.flow_vol_in[0] >= 0.81)
        m.fs.ro1_press_constr2 = Constraint(expr=m.fs.ro_first_stage.feed.pressure[0] <= 14)
        m.fs.ro2_press_constr2 = Constraint(expr=m.fs.ro_second_stage.feed.pressure[0] <= 18)
        m.fs.ro_area_constr1 = Constraint(expr=m.fs.ro_first_stage.membrane_area[0] / m.fs.ro_second_stage.membrane_area[0] <= 2.1)
        m.fs.ro_area_constr2 = Constraint(expr=m.fs.ro_first_stage.membrane_area[0] / m.fs.ro_second_stage.membrane_area[0] >= 1.9)  # m.fs.ro_first_stage.a.unfix()  # m.fs.ro_second_stage.a.unfix()  # m.fs.ro_first_stage.b.unfix()  # m.fs.ro_second_stage.b.unfix()

    if case_study == 'emwd':
        if scenario in ['baseline', 'dwi']:
            m.fs.manifee_area_constr = Constraint(expr=m.fs.menifee_a.membrane_area[0] == m.fs.menifee_b.membrane_area[0])
            m.fs.perris_area_constr = Constraint(expr=m.fs.perris_i_a.membrane_area[0] == m.fs.perris_i_b.membrane_area[0])
            m.fs.menifee_pressure_constr1 = Constraint(expr=m.fs.menifee_a.feed.pressure[0] <= 14)
            m.fs.menifee_pressure_constr2 = Constraint(expr=m.fs.menifee_a.feed.pressure[0] == m.fs.menifee_b.feed.pressure[0])
            m.fs.perris_pressure_constr1 = Constraint(expr=m.fs.perris_i_a.feed.pressure[0] <= 14)
            m.fs.perris_pressure_constr2 = Constraint(expr=m.fs.perris_i_a.feed.pressure[0] == m.fs.perris_i_b.feed.pressure[0])
            m.fs.perris_recov_constr1 = Constraint(expr=m.fs.perris_i_a.flow_vol_out[0] / m.fs.perris_i_a.flow_vol_in[0] <= 0.75)
            m.fs.perris_recov_constr1 = Constraint(expr=m.fs.perris_i_a.flow_vol_out[0] / m.fs.perris_i_a.flow_vol_in[0] >= 0.70)
            m.fs.area_constr1 = Constraint(expr=(m.fs.perris_i_a.membrane_area[0] + m.fs.perris_i_b.membrane_area[0]) / (m.fs.menifee_a.membrane_area[0] + m.fs.menifee_b.membrane_area[0]) >= 1.4)
            m.fs.area_constr2 = Constraint(expr=(m.fs.perris_i_a.membrane_area[0] + m.fs.perris_i_b.membrane_area[0]) / (m.fs.menifee_a.membrane_area[0] + m.fs.menifee_b.membrane_area[0]) <= 1.6)

        elif 'zld' in scenario:
            m.fs.first_pass_press_constr1 = Constraint(expr=m.fs.menifee_first_pass.feed.pressure[0] <= 14)
            m.fs.first_pass_press_constr2 = Constraint(expr=m.fs.menifee_first_pass.feed.pressure[0] == m.fs.perris_i_first_pass.feed.pressure[0])
            m.fs.second_pass_press_constr1 = Constraint(expr=m.fs.menifee_second_pass.feed.pressure[0] <= 18)
            m.fs.second_pass_press_constr2 = Constraint(expr=m.fs.menifee_second_pass.feed.pressure[0] == m.fs.perris_i_second_pass.feed.pressure[0])
            m.fs.area_constr1 = Constraint(expr=(m.fs.perris_i_first_pass.membrane_area[0] + m.fs.perris_i_second_pass.membrane_area[0]) / (m.fs.menifee_first_pass.membrane_area[0] + m.fs.menifee_second_pass.membrane_area[0]) >= 1.4)
            m.fs.area_constr2 = Constraint(expr=(m.fs.perris_i_first_pass.membrane_area[0] + m.fs.perris_i_second_pass.membrane_area[0]) / (m.fs.menifee_first_pass.membrane_area[0] + m.fs.menifee_second_pass.membrane_area[0]) <= 1.6)
            m.fs.ro_area_constr1 = Constraint(expr=m.fs.menifee_first_pass.membrane_area[0] <= m.fs.menifee_second_pass.membrane_area[0])
            m.fs.ro_area_constr2 = Constraint(expr=m.fs.perris_i_first_pass.membrane_area[0] <= m.fs.perris_i_second_pass.membrane_area[0])
            m.fs.area_ratio_constr1 = Constraint(expr=(m.fs.menifee_first_pass.membrane_area[0] / m.fs.menifee_second_pass.membrane_area[0]) == (m.fs.perris_i_first_pass.membrane_area[0] / m.fs.perris_i_second_pass.membrane_area[0]))

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

    if case_study == 'irwin':
        m.fs.brine_concentrator.water_recovery.fix(0.8)

    return m


def connected_units(u, temp_pfd_dict, units=[]):
    if isinstance(u, list):
        for unit in u:
            next_unit = temp_pfd_dict[unit]['ToUnitName']
            if next_unit in units or next_unit is np.nan:
                continue
            if isinstance(next_unit, list):
                units += [n for n in next_unit]
            else:
                units.append(next_unit)
            connected_units(next_unit, temp_pfd_dict, units=units)
        return units
    if u is np.nan:
        return units
    # try:
    next_unit = temp_pfd_dict[u]['ToUnitName']
    # except KeyError as e:
    #     units.append(u)
    #     return units
    if next_unit is np.nan:
        # print('next_unit is np.nan')
        return units
    if isinstance(next_unit, list):
        for unit in next_unit:
            if unit in units:
                continue
            units.append(unit)
            connected_units(unit, temp_pfd_dict, units=units)
        return units
    else:
        if next_unit in units:
            return units
        units.append(next_unit)
        connected_units(next_unit, temp_pfd_dict, units=units)
        return units

def make_decision(m, case_study, scenario):

    m.fs.units_to_drop = units_to_drop = []
    m.fs.units_to_keep = units_to_keep = []
    all_dropped_units = []

    for splitter_name, splitter_info in m.fs.all_splitters.items():
        remove_units = []
        if splitter_info['indicator']:
            splitter = getattr(m.fs, splitter_name)
            from_unit = splitter._split_from_unit
            for out in splitter.outlet_list:
                disjunct = getattr(splitter, f'disjunct_{out}')
                outlet = getattr(splitter, out)
                if bool(disjunct.indicator_var):
                    chosen_unit = outlet.to_unit
                else:
                    remove_units.append(outlet.to_unit)
                    all_dropped_units.append(outlet.to_unit)
        else:
            continue

        df_units = m.fs.df_units.set_index(['UnitName']).drop(index=remove_units).copy()
        from_unit_series = df_units.loc[from_unit].copy()
        from_unit_params = ast.literal_eval(from_unit_series.Parameter)
        from_unit_series.Parameter = str({k: v for k, v in from_unit_params.items() if k != 'split_fraction'})
        to_unit_name = []
        from_port = []
        for unit, port in zip(from_unit_series.ToUnitName.split(','), from_unit_series.FromPort.split(',')):
            if unit == chosen_unit:
                to_unit_name.append(unit)
                from_port.append(port)
                continue
            if port == 'waste':
                to_unit_name.append(unit)
                from_port.append(port)
                continue
        from_unit_series.ToUnitName = ','.join(to_unit_name)
        from_unit_series.FromPort = ','.join(from_port)
        df_units.loc[from_unit] = from_unit_series
        df_units.reset_index(inplace=True)

        temp_pfd_dict = get_pfd_dict(df_units)

        for remove in remove_units: 
            start_u = m.fs.pfd_dict[remove]['ToUnitName']
            if isinstance(start_u, list):
                temp_drop = connected_units(start_u, temp_pfd_dict, units=[s for s in start_u])
            else:
                print('else')
                temp_drop = connected_units(start_u, temp_pfd_dict, units=[start_u])
            units_to_drop += temp_drop
        temp_keep = connected_units(from_unit, temp_pfd_dict, units=[])
        units_to_keep += temp_keep
    
    units_to_keep = list(set(units_to_keep))
    units_to_drop = [u for u in list(set(units_to_drop)) if u not in units_to_keep]
    all_dropped_units += units_to_drop
    df_units = df_units.set_index('UnitName').drop(index=units_to_drop).copy()
    df_units.reset_index(inplace=True)

    m = watertap_setup(case_study=case_study, scenario=scenario, new_df_units=df_units)
    m.fs.all_dropped_units = all_dropped_units
    m = get_case_study(m=m, new_df_units=df_units)

    return m

