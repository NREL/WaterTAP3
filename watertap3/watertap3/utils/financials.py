##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2020, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
##############################################################################

import pandas as pd
from pyomo.environ import (Block, Expression, Param, Var, NonNegativeReals, units as pyunits)

from .ml_regression import get_linear_regression

__all__ = ['SystemSpecs', 'get_complete_costing', 'get_ind_table', 'get_system_specs',
           'get_system_costing', 'global_costing_parameters']

last_year_for_cost_indicies = 2050


class SystemSpecs():

    def __init__(self, train=None):
        basis_data = pd.read_csv('data/case_study_basis.csv', index_col='case_study')
        elec_cost = pd.read_csv('data/electricity_costs.csv', index_col='location')
        elec_cost.index = elec_cost.index.str.lower()
        case_study = train['case_study']
        scenario = train['scenario']
        print(str(case_study).replace('_', ' ').swapcase() + ':', str(scenario).replace('_', ' ').swapcase())
        self.location = basis_data[basis_data['variable'] == 'location_basis'].loc[case_study].value
        self.elec_price = float(elec_cost.loc[self.location])
        self.land_cost_percent_FCI = float(basis_data[basis_data['variable'] == 'land_cost_percent'].loc[case_study].value)
        self.working_cap_percent_FCI = float(basis_data[basis_data['variable'] == 'working_capital_percent'].loc[case_study].value)
        self.salaries_percent_FCI = float(basis_data[basis_data['variable'] == 'base_salary_per_fci'].loc[case_study].value)
        self.maintenance_costs_percent_FCI = float(basis_data[basis_data['variable'] == 'maintenance_cost_percent'].loc[case_study].value)
        self.lab_fees_percent_FCI = float(basis_data[basis_data['variable'] == 'laboratory_fees_percent'].loc[case_study].value)
        self.insurance_taxes_percent_FCI = float(basis_data[basis_data['variable'] == 'insurance_and_taxes_percent'].loc[case_study].value)
        self.benefit_percent_of_salary = float(basis_data[basis_data['variable'] == 'employee_benefits_percent'].loc[case_study].value)
        self.plant_lifetime_yrs = int(basis_data[basis_data['variable'] == 'plant_life_yrs'].loc[case_study].value)
        self.analysis_yr_cost_indices = int(basis_data[basis_data['variable'] == 'analysis_year'].loc[case_study].value)
        self.debt_interest_rate = float(basis_data[basis_data['variable'] == 'debt_interest_rate'].loc[case_study].value)
        self.plant_cap_utilization = float(basis_data[basis_data['variable'] == 'plant_cap_utilization'].loc[case_study].value)


def create_costing_block(unit, basis_year, tpec_or_tic):
    '''
    Function to create costing block and establish basis year and TPEC/TIC factor for each
    WaterTAP3 unit.

    :param unit: WaterTAP3 unit
    :type unit: str
    :param basis_year: Basis year for adjusting cost calculations
    :type basis_year: str
    :param tpec_or_tic: either 'TPEC' or 'TIC'; determines which factor to use for FCI adjustment
    (if necessary)
    :type tpec_or_tic: str
    :return:
    '''
    unit.costing = costing = Block()
    costing.basis_year = basis_year
    sys_cost_params = unit.parent_block().costing_param
    if tpec_or_tic == 'TPEC':
        costing.tpec_tic = unit.tpec_tic = sys_cost_params.tpec
    else:
        costing.tpec_tic = unit.tpec_tic = sys_cost_params.tic


def get_complete_costing(costing):
    '''
    Function to build costing block for each WaterTAP3 unit.

    :param costing: Costing block object from WaterTAP3 unit model.
    :type costing: object
    :return:
    '''
    unit = costing.parent_block()
    basis_year = costing.basis_year
    sys_specs = unit.parent_block().costing_param
    time = unit.flowsheet().config.time
    t = time.first()
    chem_dict = unit.chem_dict
    electricity = unit.electricity

    df = get_ind_table(sys_specs.analysis_yr_cost_indices)
    costing.cap_replacement_parts = df.loc[basis_year].Capital_Factor
    costing.catalysts_chemicals = df.loc[basis_year].CatChem_Factor
    costing.labor_and_other_fixed = df.loc[basis_year].Labor_Factor
    costing.consumer_price_index = df.loc[basis_year].CPI_Factor

    costing.uncertainty_multiplier_fci = Var(time,
                                             domain=NonNegativeReals,
                                             initialize=0,
                                             doc='Uncertainty Multiplier for FCI')

    costing.wt3_error_fci = Var(time,
                                domain=NonNegativeReals,
                                initialize=1,
                                doc='Standard WT3 Error for FCI')

    costing.uncertainty_multiplier_fci.fix(0)
    costing.wt3_error_fci.fix(1)

    costing.uncertainty_multiplier_om = Var(time,
                                            domain=NonNegativeReals,
                                            initialize=0,
                                            doc='Uncertainty Multiplier for Fixed O&M')

    costing.wt3_error_om = Var(time,
                               domain=NonNegativeReals,
                               initialize=1,
                               doc='Standard WT3 Error for Fixed O&M')

    costing.uncertainty_multiplier_om.fix(0)
    costing.wt3_error_om.fix(1)

    costing.fixed_cap_inv = ((costing.fixed_cap_inv_unadjusted * costing.cap_replacement_parts) * (1 - costing.uncertainty_multiplier_fci[t])) * costing.wt3_error_fci[t]

    # if unit.unit_name == 'evaporation_pond':
    #     costing.land_cost = 0
    # else:
    costing.land_cost = costing.fixed_cap_inv * sys_specs.land_cost_percent_FCI
    costing.working_cap = costing.fixed_cap_inv * sys_specs.working_cap_percent_FCI
    costing.total_cap_investment = costing.fixed_cap_inv + costing.land_cost + costing.working_cap

    flow_in_m3yr = pyunits.convert(costing.parent_block().flow_vol_in[t],
                                   to_units=pyunits.m ** 3 / pyunits.year)

    ## cat and chems ##
    cat_chem_df = pd.read_csv('data/catalyst_chemicals.csv', index_col='Material')
    chem_cost_sum = 0
    for key in chem_dict.keys():
        if key == 'unit_cost':
            chem_cost_sum = chem_dict[key] * costing.fixed_cap_inv * 1E6
        else:
            chem_cost = cat_chem_df.loc[key].Price
            chem_cost_sum += costing.catalysts_chemicals * flow_in_m3yr * chem_cost * chem_dict[key] * sys_specs.plant_cap_utilization

    costing.uncertainty_multiplier_catchem = Var(time,
                                                 domain=NonNegativeReals,
                                                 initialize=0,
                                                 doc='Uncertainty Multiplier for Catalysts/Chemicals')

    costing.wt3_error_catchem = Var(time,
                                    domain=NonNegativeReals,
                                    initialize=1,
                                    doc='Standard WT3 Error for Catalysts/Chemicals')

    costing.uncertainty_multiplier_catchem.fix(0)
    costing.wt3_error_catchem.fix(1)

    costing.cat_and_chem_cost = Expression(expr=((chem_cost_sum * 1E-6) * (1 - costing.uncertainty_multiplier_catchem[t])) * costing.wt3_error_catchem[t])

    if not hasattr(costing, 'electricity_cost'):
        costing.electricity_cost = Expression(expr=(electricity * flow_in_m3yr * sys_specs.electricity_price * 1E-6) * sys_specs.plant_cap_utilization,
                                              doc='Electricity cost')  # M$/yr

    if not hasattr(costing, 'other_var_cost'):
        costing.other_var_cost = 0

    costing.base_employee_salary_cost = costing.fixed_cap_inv_unadjusted * sys_specs.salaries_percent_FCI
    costing.salaries = Expression(expr=costing.labor_and_other_fixed * costing.base_employee_salary_cost, doc='Salaries')
    costing.benefits = costing.salaries * sys_specs.benefit_percent_of_salary
    costing.maintenance = sys_specs.maintenance_costs_percent_FCI * costing.fixed_cap_inv
    costing.lab = sys_specs.lab_fees_percent_FCI * costing.fixed_cap_inv
    costing.insurance_taxes = sys_specs.insurance_taxes_percent_FCI * costing.fixed_cap_inv
    costing.total_fixed_op_cost = Expression(expr=((costing.salaries + costing.benefits + costing.maintenance + costing.lab + costing.insurance_taxes) * (1 - costing.uncertainty_multiplier_om[t])) * costing.wt3_error_om[t])
    costing.annual_op_main_cost = costing.cat_and_chem_cost + costing.electricity_cost + costing.other_var_cost + costing.total_fixed_op_cost
    costing.total_operating_cost = costing.total_fixed_op_cost + costing.cat_and_chem_cost + costing.electricity_cost + costing.other_var_cost


def get_ind_table(analysis_yr_cost_indices):
    '''
    Function to get costing indicies for WaterTAP3 model.

    :param analysis_yr_cost_indices: Year to get costing indices for.
    :type analysis_yr_cost_indices: int
    :return: Indicies DataFrame
    '''
    df = pd.read_csv('data/plant_cost_indices.csv')

    df1 = pd.DataFrame()
    for name in df.columns[1:]:
        a, b = get_linear_regression(list(df.Year), list(df[('%s' % name)]), name)
        new_list = []
        yr_list = []
        for yr in range(df.Year.max() + 1, last_year_for_cost_indicies + 1):
            new_list.append(a * yr + b)
            yr_list.append(yr)
        df1[name] = new_list
    df1['Year'] = yr_list
    df = pd.concat([df, df1], axis=0)

    new_cost_variables = ['Capital', 'CatChem', 'Labor', 'CPI']
    for variable in new_cost_variables:
        ind_name = '%s_Index' % variable
        fac_name = '%s_Factor' % variable
        df[fac_name] = (df[df.Year == analysis_yr_cost_indices][ind_name].max() / df[ind_name])
    df = df.set_index(df.Year)
    df = df.replace(1.0, 1.00000000001)

    return df


def get_system_specs(m_fs):
    '''
    Function to set costing parameters for WaterTAP3 model.


    '''
    m_fs.costing_param = Block()
    b = m_fs.costing_param

    b.electricity_price = Var(initialize=0.07,
                              doc='Electricity cost [$/kWh]')
    b.maintenance_costs_percent_FCI = Var(initialize=0.07,
                                          doc='Maintenance/contingency cost as % FCI')
    b.salaries_percent_FCI = Var(initialize=0.07,
                                 doc='Salaries cost as % FCI')
    b.benefit_percent_of_salary = Var(initialize=0.07,
                                      doc='Benefits cost as % FCI')
    b.insurance_taxes_percent_FCI = Var(initialize=0.07,
                                        doc='Insurance/taxes cost as % FCI')
    b.lab_fees_percent_FCI = Var(initialize=0.07,
                                 doc='Lab cost as % FCI')
    b.land_cost_percent_FCI = Var(initialize=0.07,
                                  doc='Land cost as % FCI')
    b.plant_lifetime_yrs = Var(initialize=30,
                               doc='Plant lifetime [years')
    b.plant_cap_utilization = Var(initialize=1,
                                  doc='Plant capacity utilization [%]')
    b.working_cap_percent_FCI = Var(initialize=0.008,
                                    doc='Working capital as % FCI')
    b.wacc = Var(initialize=0.05,
                 doc='Weighted Average Cost of Capital (WACC)')

    # ADD THE REST AS VARIABLES.

    system_specs = SystemSpecs(m_fs.train)

    b.electricity_price.fix(system_specs.elec_price)
    b.salaries_percent_FCI.fix(system_specs.salaries_percent_FCI)
    b.land_cost_percent_FCI.fix(system_specs.land_cost_percent_FCI)
    b.maintenance_costs_percent_FCI.fix(system_specs.maintenance_costs_percent_FCI)
    b.lab_fees_percent_FCI.fix(system_specs.lab_fees_percent_FCI)
    b.insurance_taxes_percent_FCI.fix(system_specs.insurance_taxes_percent_FCI)
    b.plant_lifetime_yrs.fix(system_specs.plant_lifetime_yrs)

    b.benefit_percent_of_salary.fix(system_specs.benefit_percent_of_salary)
    b.working_cap_percent_FCI.fix(system_specs.working_cap_percent_FCI)
    b.plant_cap_utilization.fix(system_specs.plant_cap_utilization)  # 1.0
    b.analysis_yr_cost_indices = system_specs.analysis_yr_cost_indices
    b.wacc.fix(system_specs.debt_interest_rate)

    b.location = system_specs.location

    b.tpec = 3.4
    b.tic = 1.65


def get_system_costing(self):
    '''
    Function to aggregate unit model results for calculation of system costing for WaterTAP3 model.

    '''
    if not hasattr(self, 'costing'):
        self.costing = Block()
    b = self.costing
    time = unit.flowsheet().config.time
    t = time.first()
    sys_specs = self.costing_param

    total_capital_investment_var_lst = []
    cat_and_chem_cost_lst = []
    electricity_cost_lst = []
    other_var_cost_lst = []
    total_fixed_op_cost_lst = []
    electricity_intensity_lst = []

    wacc = sys_specs.wacc

    # b.wacc = Var(initialize=sys_specs.wacc,
    #              doc='Weighted average cost of capital (WACC)')
    #
    # b.wacc.fix(sys_specs.wacc)

    b.capital_recovery_factor = (wacc * (1 + wacc) ** sys_specs.plant_lifetime_yrs) / (
            ((1 + wacc) ** sys_specs.plant_lifetime_yrs) - 1)

    for b_unit in self.component_objects(Block, descend_into=True):
        if hasattr(b_unit, 'costing'):
            total_capital_investment_var_lst.append(b_unit.costing.total_cap_investment)
            cat_and_chem_cost_lst.append(b_unit.costing.cat_and_chem_cost)
            electricity_cost_lst.append(b_unit.costing.electricity_cost)
            other_var_cost_lst.append(b_unit.costing.other_var_cost)
            total_fixed_op_cost_lst.append(b_unit.costing.total_fixed_op_cost)

    b.sys_tci_reduction = Var(time,
                                domain=NonNegativeReals,
                                initialize=1,
                                doc='System TCI reduction factor')

    b.sys_chem_reduction = Var(time,
                                 domain=NonNegativeReals,
                                 initialize=1,
                                 doc='System catalyst/chemical cost reduction factor')

    b.sys_elect_reduction = Var(time,
                                  domain=NonNegativeReals,
                                  initialize=1,
                                  doc='System electricity cost reduction factor')

    b.sys_other_reduction = Var(time,
                                  domain=NonNegativeReals,
                                  initialize=1,
                                  doc='System other cost reduction factor')

    b.sys_fixed_op_reduction = Var(time,
                                     domain=NonNegativeReals,
                                     initialize=1,
                                     doc='System fixed O&M reduction factor')

    b.sys_total_op_reduction = Var(time,
                                     domain=NonNegativeReals,
                                     initialize=1,
                                     doc='System total O&M reduction factor')

    b.sys_tci_reduction.fix(0)
    b.sys_chem_reduction.fix(0)
    b.sys_elect_reduction.fix(0)
    b.sys_other_reduction.fix(0)
    b.sys_fixed_op_reduction.fix(0)
    b.sys_total_op_reduction.fix(0)

    b.sys_tci_uncertainty = Var(time,
                              domain=NonNegativeReals,
                              initialize=1,
                              doc='System TCI uncertainty factor')

    b.sys_chem_uncertainty = Var(time,
                               domain=NonNegativeReals,
                               initialize=1,
                               doc='System catalyst/chemical cost uncertainty factor')

    b.sys_elect_uncertainty = Var(time,
                                domain=NonNegativeReals,
                                initialize=1,
                                doc='System electricity cost uncertainty factor')

    b.sys_other_uncertainty = Var(time,
                                domain=NonNegativeReals,
                                initialize=1,
                                doc='System other cost uncertainty factor')

    b.sys_fixed_op_uncertainty = Var(time,
                                   domain=NonNegativeReals,
                                   initialize=1,
                                   doc='System fixed O&M uncertainty factor')

    b.sys_total_op_uncertainty = Var(time,
                                   domain=NonNegativeReals,
                                   initialize=1,
                                   doc='System total O&M uncertainty factor')

    b.sys_tci_uncertainty.fix(1)
    b.sys_chem_uncertainty.fix(1)
    b.sys_elect_uncertainty.fix(1)
    b.sys_other_uncertainty.fix(1)
    b.sys_fixed_op_uncertainty.fix(1)
    b.sys_total_op_uncertainty.fix(1)

    b.capital_investment_total = Expression(expr=(sum(total_capital_investment_var_lst) * (1 - b.sys_tci_reduction[t])) * b.sys_tci_uncertainty[t])
    b.cat_and_chem_cost_total = Expression(expr=((sum(cat_and_chem_cost_lst) * self.costing_param.plant_lifetime_yrs) * (1 - b.sys_chem_reduction[t])) * b.sys_chem_uncertainty[t])
    b.electricity_cost_total = Expression(expr=((sum(electricity_cost_lst) * self.costing_param.plant_lifetime_yrs) * (1 - b.sys_elect_reduction[t])) * b.sys_elect_uncertainty[t])
    b.other_var_cost_total = Expression(expr=(sum(other_var_cost_lst) * self.costing_param.plant_lifetime_yrs) * (1 - b.sys_other_reduction[t]))
    b.fixed_op_cost_total = Expression(expr=(sum(total_fixed_op_cost_lst) * self.costing_param.plant_lifetime_yrs) * (1 - b.sys_fixed_op_reduction[t]))
    b.operating_cost_total = Expression(expr=(b.fixed_op_cost_total + b.cat_and_chem_cost_total + b.electricity_cost_total + b.other_var_cost_total) * (1 - b.sys_total_op_reduction[t]))
    b.cat_and_chem_cost_annual = Expression(expr=sum(cat_and_chem_cost_lst))
    b.electricity_cost_annual = Expression(expr=sum(electricity_cost_lst))
    b.other_var_cost_annual = Expression(expr=sum(other_var_cost_lst))
    b.fixed_op_cost_annual = Expression(expr=sum(total_fixed_op_cost_lst))
    b.operating_cost_annual = Expression(expr=(b.fixed_op_cost_annual + b.cat_and_chem_cost_annual + b.electricity_cost_annual + b.other_var_cost_annual))

    recovered_water_flow = 0
    wastewater_list = []

    time = self.config.time.first()

    for b_unit in self.component_objects(Block, descend_into=False):
        if hasattr(b_unit, 'outlet'):
            if len(getattr(b_unit, 'outlet').arcs()) == 0:
                if hasattr(b_unit.parent_block(), 'pfd_dict'):
                    if b_unit.parent_block().pfd_dict[str(b_unit)[3:]]['Type'] == 'use':
                        recovered_water_flow = recovered_water_flow + b_unit.flow_vol_out[time]
                else:
                    if 'reverse_osmosis' in str(b_unit):
                        recovered_water_flow = recovered_water_flow + b_unit.flow_vol_out[time]
                    if 'cooling_tower' in str(b_unit):
                        recovered_water_flow = recovered_water_flow + b_unit.flow_vol_out[time]

    b.treated_water = recovered_water_flow

    b.sum_of_inflow = sum_of_inflow = 0
    for key in b.parent_block().flow_in_dict.keys():
        sum_of_inflow += getattr(self, key).flow_vol_in[time]

    b.system_recovery = b.treated_water / sum_of_inflow

    # LCOW for each unit
    for b_unit in self.component_objects(Block, descend_into=True):
        if hasattr(b_unit, 'costing'):
            setattr(b_unit, 'LCOW', Expression(
                    expr=1E6 * (b_unit.costing.total_cap_investment * b.capital_recovery_factor + b_unit.costing.annual_op_main_cost) /
                         (b.treated_water * 3600 * 24 * 365 * sys_specs.plant_cap_utilization),
                    doc='Unit Levelized Cost of Water [$/m3]'))

            setattr(b_unit, 'LCOW_TCI', Expression(
                    expr=1E6 * (b_unit.costing.total_cap_investment * b.capital_recovery_factor) /
                         (b.treated_water * 3600 * 24 * 365 * sys_specs.plant_cap_utilization),
                    doc='Unit TCI Levelized Cost of Water [$/m3]'))

            setattr(b_unit, 'LCOW_elec', Expression(
                    expr=1E6 * (b_unit.costing.electricity_cost) /
                         (b.treated_water * 3600 * 24 * 365 * sys_specs.plant_cap_utilization),
                    doc='Unit Electricity Levelized Cost of Water [$/m3]'))

            setattr(b_unit, 'LCOW_fixed_op', Expression(
                    expr=1E6 * (b_unit.costing.total_fixed_op_cost) /
                         (b.treated_water * 3600 * 24 * 365 * sys_specs.plant_cap_utilization),
                    doc='Unit Fixed Operating Levelized Cost of Water [$/m3]'))

            setattr(b_unit, 'LCOW_chem', Expression(
                    expr=1E6 * (b_unit.costing.cat_and_chem_cost) /
                         (b.treated_water * 3600 * 24 * 365 * sys_specs.plant_cap_utilization),
                    doc='Unit Chemical Levelized Cost of Water [$/m3]'))

            setattr(b_unit, 'LCOW_other', Expression(
                    expr=1E6 * (b_unit.costing.other_var_cost) /
                         (b.treated_water * 3600 * 24 * 365 * sys_specs.plant_cap_utilization),
                    doc='Unit Other O&M Levelized Cost of Water [$/m3]'))

            setattr(b_unit, 'LCOW_total_op', Expression(
                    expr=1E6 * (b_unit.costing.total_operating_cost) /
                         (b.treated_water * 3600 * 24 * 365 * sys_specs.plant_cap_utilization),
                    doc='Unit Total Operating Levelized Cost of Water [$/m3]'))

            setattr(b_unit, 'elec_int_treated', Expression(
                    expr=(b_unit.costing.electricity_cost * 1E6 / b.parent_block().costing_param.electricity_price) /
                         (b.treated_water * 3600 * 24 * 365),
                    doc='Unit Electricity Intensity [kWh/m3]'))

    # LCOW by cost category
    b.LCOW_TCI = Expression(expr=1E6 * (b.capital_investment_total * b.capital_recovery_factor) / (
            b.treated_water * 3600 * 24 * 365 * sys_specs.plant_cap_utilization))

    b.LCOW_elec = Expression(expr=1E6 * (b.electricity_cost_annual) / (
            b.treated_water * 3600 * 24 * 365 * sys_specs.plant_cap_utilization))

    b.LCOW_fixed_op = Expression(expr=1E6 * (b.fixed_op_cost_annual) / (
            b.treated_water * 3600 * 24 * 365 * sys_specs.plant_cap_utilization))

    b.LCOW_chem = Expression(expr=1E6 * (b.cat_and_chem_cost_annual) / (
            b.treated_water * 3600 * 24 * 365 * sys_specs.plant_cap_utilization))

    b.LCOW_other_onm = Expression(expr=1E6 * (b.other_var_cost_annual) / (
            b.treated_water * 3600 * 24 * 365 * sys_specs.plant_cap_utilization))

    ## GET TOTAL ELECTRICITY CONSUMPTION IN kwh/m3 of treated water
    b.electricity_intensity = Expression(
            expr=(b.electricity_cost_annual * 1E6 / b.parent_block().costing_param.electricity_price) /
                 (b.treated_water * 3600 * 24 * 365),
            doc='Electricity Intensity [kWh/m3]')

    b.LCOW = Expression(
            expr=1E6 * (b.capital_investment_total * b.capital_recovery_factor + b.operating_cost_annual) /
                 (b.treated_water * 3600 * 24 * 365 * sys_specs.plant_cap_utilization),
            doc='Levelized Cost of Water [$/m3]')

    b.LCOW_inflow = Expression(
            expr=1E6 * (b.capital_investment_total * b.capital_recovery_factor + b.operating_cost_annual) /
                 (sum_of_inflow * 3600 * 24 * 365 * sys_specs.plant_cap_utilization),
            doc='Levelized Cost of Water by influent flow [$/m3]')

    b.elec_frac_LCOW = Expression(
            expr=((1E6 * (b.electricity_cost_annual) /
                   (b.treated_water * 3600 * 24 * 365 * sys_specs.plant_cap_utilization))) / b.LCOW,
            doc='Electricity cost as fraction of LCOW')


def global_costing_parameters(self, year=None):
    if year is None:
        year = '2018'
    ce_index_dic = {
            '2019': 680,
            '2018': 671.1,
            '2017': 567.5,
            '2016': 541.7,
            '2015': 556.8,
            '2014': 576.1,
            '2013': 567.3,
            '2012': 584.6,
            '2011': 585.7,
            '2010': 550.8
            }

    self.CE_index = Param(mutable=True, initialize=ce_index_dic[year],
                          doc='Chemical Engineering Plant Cost Index $ year')