##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2020, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes-pse".
##############################################################################
"""
This is fairly basic at this stage, as I didn't try too hard to understand the
calcualtions.

Note that costing in IDAES is still a fairly new feature, and is still in the
prototype phase. Notably, we have only really looked at capital costs so far,
and there is probably a alack of support for operating costs for now.

However, this is where you would write methods for calculating costs for each
type of unit operation. The goal would be to write these in a way that would
work for both WaterTAP3 and ProteusLib. This should be possible as long as we
clearly document what variables are required for the cost methods and what they
are called (ideally using the standard IDAES naming conventions where
appropriate)
"""
from pyomo.environ import (
    Block, Constraint, Expression, Var, Param, NonNegativeReals, units as pyunits)
from idaes.core.util.exceptions import ConfigurationError

import pandas as pd
import ml_regression
import case_study_trains

global train
global source_water
global pfd_dict

# TO DO - MOVE TO WHERE NEEDED -> global_costing_parameters


last_year_for_cost_indicies = 2050
on_stream_factor = 1.0
 
# This first method is used at the flowsheet level and contains any global
# parameters and methods


class SystemSpecs():
  
    def __init__(self, train = None):
        
        basis_data = pd.read_csv('data/case_study_basis.csv', index_col='case_study')
        elec_cost = pd.read_csv('data/electricity_costs.csv', index_col='location')
        
        case_study = train["case_study"]
        print(case_study)
        location = basis_data[basis_data['variable'] == 'location_basis'].loc[case_study].value
        
        self.elec_price = float(elec_cost.loc[location])
        self.salaries_percent_FCI = float(basis_data[basis_data['variable'] == 'base_salary_per_FCI'].loc[case_study].value)  
        self.land_cost_percent_FCI = float(basis_data[basis_data['variable'] == 'land_cost_percent'].loc[case_study].value)
        self.working_cap_percent_FCI = float(basis_data[basis_data['variable'] ==
                                                        'working_capital_percent'].loc[case_study].value)

        self.maintinance_costs_percent_FCI = float(basis_data[basis_data['variable'] == 
                                                              'maintenance_cost_percent'].loc[case_study].value)
        self.lab_fees_percent_FCI = float(basis_data[basis_data['variable'] == 'laboratory_fees_percent'].loc[case_study].value)

        self.insurance_taxes_percent_FCI = float(basis_data[basis_data['variable'] == 
                                                            'insurance_and_taxes_percent'].loc[case_study].value)
        self.benefit_percent_of_salary = float(basis_data[basis_data['variable'] == 
                                                          'employee_benefits_percent'].loc[case_study].value) 
        self.plant_lifetime_yrs = int(basis_data[basis_data['variable'] == 'plant_life_yrs'].loc[case_study].value)
        self.analysis_yr_cost_indicies = int(basis_data[basis_data['variable'] == 'analysis_year'].loc[case_study].value)

    

################## WATERTAP METHOD ###########################################################

def get_complete_costing(self):
    
    sys_specs = self.parent_block().parent_block().costing_param
    time = self.parent_block().flowsheet().config.time.first()
    chem_dict = self.parent_block().chem_dict
    electricity = self.parent_block().electricity
    
    df = get_ind_table(sys_specs.analysis_yr_cost_indicies)
    self.cap_replacement_parts = df.loc[self.basis_year].Capital_Factor
    self.catalysts_chemicals = df.loc[self.basis_year].CatChem_Factor
    self.labor_and_other_fixed = df.loc[self.basis_year].Labor_Factor
    self.consumer_price_index = df.loc[self.basis_year].CPI_Factor

    self.fixed_cap_inv = self.fixed_cap_inv_unadjusted * self.cap_replacement_parts
    self.land_cost = self.fixed_cap_inv * sys_specs.land_cost_percent_FCI
    self.working_cap = self.fixed_cap_inv * sys_specs.working_cap_percent_FCI 
    self.total_cap_investment = self.fixed_cap_inv + self.land_cost + self.working_cap

    flow_in_m3yr = (pyunits.convert(self.parent_block().flow_vol_in[time], to_units=pyunits.m**3/pyunits.year))
    
    ## cat and chems ##
    cat_chem_df = pd.read_csv('data/catalyst_chemicals.csv', index_col = "Material")
    chem_cost_sum = 0 
    for key in chem_dict.keys():
        chem_cost = cat_chem_df.loc[key].Price
        chem_cost_sum = chem_cost_sum + self.catalysts_chemicals * flow_in_m3yr * chem_cost * chem_dict[key] * on_stream_factor
    self.cat_and_chem_cost = chem_cost_sum
        
    self.electricity_cost = Expression(
            expr= (electricity * flow_in_m3yr * sys_specs.electricity_price/1000000),
            doc="Electricity cost") # M$/yr
    self.other_var_cost = 0

    self.base_employee_salary_cost = self.fixed_cap_inv_unadjusted * sys_specs.salaries_percent_FCI
    self.salaries = Expression(
            expr= self.labor_and_other_fixed * self.base_employee_salary_cost,
            doc="Salaries")
    self.benefits = self.salaries * sys_specs.benefit_percent_of_salary
    self.maintenance = sys_specs.maintinance_costs_percent_FCI * self.fixed_cap_inv
    self.lab = sys_specs.lab_fees_percent_FCI * self.fixed_cap_inv
    self.insurance_taxes = sys_specs.insurance_taxes_percent_FCI * self.fixed_cap_inv
    self.total_fixed_op_cost = Expression(
        expr = self.salaries + self.benefits + self.maintenance + self.lab + self.insurance_taxes)

    self.total_up_cost = (
        self.total_cap_investment
        + self.cat_and_chem_cost
        + self.electricity_cost
        + self.other_var_cost
        + self.total_fixed_op_cost
    )
    
    
    
# TO DO MOVE TO FUNCTION BELOW
def get_ind_table(analysis_yr_cost_indicies):
    df = pd.read_csv("data/plant_cost_indices.csv")

    df1 = pd.DataFrame()
    for name in df.columns[1:]:
        a, b = ml_regression.get_linear_regression(
            list(df.Year), list(df[("%s" % name)]), name
        )
        new_list = []
        yr_list = []
        for yr in range(df.Year.max() + 1, last_year_for_cost_indicies + 1):
            new_list.append(a * yr + b)
            yr_list.append(yr)
        df1[name] = new_list
    df1["Year"] = yr_list
    df = pd.concat([df, df1], axis=0)

    new_cost_variables = ["Capital", "CatChem", "Labor", "CPI"]
    for variable in new_cost_variables:
        ind_name = "%s_Index" % variable
        fac_name = "%s_Factor" % variable
        df[fac_name] = (
             df[df.Year == analysis_yr_cost_indicies][ind_name].max() / df[ind_name]
        )

    df = df.set_index(df.Year)
    
    df = df.replace(1.0, 1.00000000001)

    return df



####################################
###### FROM TIM's RO MODEL #######    
####################################
# The parameters below should replace the constants above.
### THIS IS NOT CURRENTLY USED --> add_costing_param_block    

def get_system_specs(self):
    self.costing_param = Block()
    b = self.costing_param

    b.electricity_price = Var(
        initialize=0.07,
        doc='Electricity cost [$/kWh]')
    
    # ADD THE REST AS VARIABLES.
    
    system_specs = SystemSpecs(train)
    
    b.electricity_price.fix(system_specs.elec_price)
    b.salaries_percent_FCI = system_specs.salaries_percent_FCI
    b.land_cost_percent_FCI = system_specs.land_cost_percent_FCI
    b.maintinance_costs_percent_FCI = system_specs.maintinance_costs_percent_FCI
    b.lab_fees_percent_FCI = system_specs.lab_fees_percent_FCI
    b.insurance_taxes_percent_FCI = system_specs.insurance_taxes_percent_FCI
    b.plant_lifetime_yrs = system_specs.plant_lifetime_yrs
    b.analysis_yr_cost_indicies = system_specs.analysis_yr_cost_indicies
    b.benefit_percent_of_salary = system_specs.benefit_percent_of_salary
    b.working_cap_percent_FCI  = system_specs.working_cap_percent_FCI

    # traditional parameters are the only Vars on the block and should be fixed
    #for v in b.component_objects(Var, descend_into=True):
    #    for i in v:
    #        if v[i].value is None:
    #            raise ConfigurationError(
    #                "{} parameter {} was not assigned"
    #                " a value. Please check your configuration "
    #                "arguments.".format(b.name, v.local_name))
    #        v[i].fix()


def get_system_costing(self):
    if not hasattr(self, 'costing'):
        self.costing = Block()
    b = self.costing

#     b.LCOW = Var(
#         initialize=1e5,
#         domain=NonNegativeReals,
#         doc='Levelized cost of water [$/m3]')
    b.capital_recovery_factor = Var(
         initialize=0.01,
         domain=NonNegativeReals,
         doc='Captial recovery factor')  
    
    total_capital_investment_var_lst = []
    cat_and_chem_cost_lst = []
    electricity_cost_lst = []
    other_var_cost_lst = []
    total_fixed_op_cost_lst = []
    
    b.capital_recovery_factor.fix(0.08)  #TODO ANNA ARIEL KURBY
    
    plant_lifetime_yrs = self.costing_param.plant_lifetime_yrs
    
    for b_unit in self.component_objects(Block, descend_into=True):
        if hasattr(b_unit, 'costing'):
            total_capital_investment_var_lst.append(b_unit.costing.total_cap_investment)
            cat_and_chem_cost_lst.append(b_unit.costing.cat_and_chem_cost)
            electricity_cost_lst.append(b_unit.costing.electricity_cost)
            other_var_cost_lst.append(b_unit.costing.other_var_cost)
            total_fixed_op_cost_lst.append(b_unit.costing.total_fixed_op_cost)
            
    #operating_cost_var_lst.append(b.operating_cost_MLC)

    b.capital_investment_total = Expression(
        expr = sum(total_capital_investment_var_lst))
    b.cat_and_chem_cost_total = Expression(
        expr=sum(cat_and_chem_cost_lst) * plant_lifetime_yrs)
    b.electricity_cost_total = Expression(
        expr=sum(electricity_cost_lst) * plant_lifetime_yrs)
    b.other_var_cost_total = Expression(
        expr=sum(other_var_cost_lst) * plant_lifetime_yrs)
    b.fixed_op_cost_total = Expression(
        expr=sum(total_fixed_op_cost_lst) * plant_lifetime_yrs)
   
    b.operating_cost_total = Expression(
        expr=(b.fixed_op_cost_total + b.cat_and_chem_cost_total + b.electricity_cost_total 
                                + b.other_var_cost_total + b.fixed_op_cost_total))
    
    
    b.capital_investment_annual = Expression(
        expr = sum(total_capital_investment_var_lst))
    b.cat_and_chem_cost_annual = Expression(
        expr=sum(cat_and_chem_cost_lst))
    b.electricity_cost_annual = Expression(
        expr=sum(electricity_cost_lst))
    b.other_var_cost_annual = Expression(
        expr=sum(other_var_cost_lst))
    b.fixed_op_cost_annual = Expression(
        expr=sum(total_fixed_op_cost_lst))
   
    b.operating_cost_annual = Expression(
        expr=(b.fixed_op_cost_annual + b.cat_and_chem_cost_annual + b.electricity_cost_annual 
                                + b.other_var_cost_annual + b.fixed_op_cost_annual))    
    
    
    #RECOVERED WATER = IF OUTLET IS NOT GOING ANYWHERE
    from case_study_trains import check_waste
    recovered_water_flow = 0
    wastewater_list = []
    
    time = self.config.time.first()
    
    for b_unit in self.component_objects(Block, descend_into=False):
        if hasattr(b_unit, 'outlet'):

            if len(getattr(b_unit, "outlet").arcs()) == 0:

                if check_waste(b_unit) == "no":
                    recovered_water_flow = recovered_water_flow + b_unit.flow_vol_in[time]
 
    b.treated_water = recovered_water_flow
   
    # TODO TOTAL WASTE = 
    ## HERE GET TOTAL ELECTRICITY CONSUMPTION IN KWH AS WELL?
    
    b.LCOW = Expression(
        expr=(1e6*(b.capital_investment_total * b.capital_recovery_factor + b.operating_cost_annual) 
    / (b.treated_water * 3600 * 24 * 365)),
    doc="Levelized Cost of Water in $/m3")
    
    
    
### JUST TO GET IDAES TO RUN --> THESE SHOULd BE THE SYSTEM SPECS    
def global_costing_parameters(self, year=None):
    # Define a default year if none is provided
    if year is None:
        year = '2018'

    # Cost index $/year (method argument or 2018 default)
    # I just took this from the IDAES costing methods as an example
    # You could also link to an external database of values, such as the
    # Excel spreadsheet
    ce_index_dic = {'2019': 680, '2018': 671.1, '2017': 567.5, '2016': 541.7,
                    '2015': 556.8, '2014': 576.1, '2013': 567.3, '2012': 584.6,
                    '2011': 585.7, '2010': 550.8}

    self.CE_index = Param(mutable=True, initialize=ce_index_dic[year],
                          doc='Chemical Engineering Plant Cost Index $ year')   
    
    
    
    