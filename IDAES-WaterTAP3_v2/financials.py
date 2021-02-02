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


# TO DO - MOVE TO WHERE NEEDED -> global_costing_parameters

# fixed_op_cost_scaling_exp = 0.7
# basis_year = 2014  # meaning:
analysis_yr_cost_indicies = 2020
last_year_for_cost_indicies = 2050
on_stream_factor = 1.0

salaries_percent_FCI = 0.001  # represented as a fraction. source:
land_cost_precent_FCI = 0.0015  # represented as a fraction. source:
working_cap_precent_FCI = 0.05  # represented as a fraction. source:
maintinance_costs_precent_FCI = 0.008
lab_fees_precent_FCI = 0.003
insurance_taxes_precent_FCI = 0.002

benefit_percent_of_salary = 0.9

elec_price = 0.134
    
plant_lifetime_yrs = 20
    
# This first method is used at the flowsheet level and contains any global
# parameters and methods

### THIS IS NOT CURRENTLY USED --> global_costing_parameters

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
    
    
   
    
# TO DO MOVE TO FUNCTION BELOW
def get_ind_table():
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



# There are a couple of variables that IDAES expects to be present
# These are fairly obvious, but have pre-defined names

### THIS IS NOT CURRENTLY USED --> _make_vars
def _make_vars(self):
    # build generic costing variables (all costing models need these vars)
    self.base_cost = Var(initialize=1e5,
                         domain=NonNegativeReals,
                         doc='Unit Base Cost cost in $')
    self.purchase_cost = Var(initialize=1e4,
                             domain=NonNegativeReals,
                             doc='Unit Purchase Cost in $')


####################################
###### FROM TIM's RO MODEL #######    
####################################
# The parameters below should replace the constants above.
### THIS IS NOT CURRENTLY USED --> add_costing_param_block    
def add_costing_param_block(self):
    self.costing_param = Block()
    b = self.costing_param

    b.load_factor = Var(
        initialize=0.9,
        doc='Load factor [fraction of uptime]')
    b.factor_total_investment = Var(
        initialize=2,
        doc='Total investment factor [investment cost/equipment cost]')
    b.factor_MLC = Var(
        initialize=0.03,
        doc='Maintenance-labor-chemical factor [fraction of investment cost/year]')
    b.factor_capital_annualization = Var(
        initialize=0.1,
        doc='Capital annualization factor [fraction of investment cost/year]')
    b.factor_membrane_replacement = Var(
        initialize=0.2,
        doc='Membrane replacement factor [fraction of membrane replaced/year]')
    b.electricity_cost = Var(
        initialize=0.07,
        doc='Electricity cost [$/kWh]')
    b.mem_cost = Var(
        initialize=30,
        doc='Membrane cost [$/m2]')
    b.hp_pump_cost = Var(
        initialize=53 / 1e5 * 3600,
        doc='High pressure pump cost [$/W]')
    b.erd_cost = Var(
        ['A', 'B'],
        initialize={'A': 3134.7, 'B': 0.58},
        doc='Energy recovery device cost parameters')

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


#     b.capital_investment_total = Var(
#         initialize=1e6,
#         domain=NonNegativeReals,
#         doc='Total investment cost [$]')
#     b.operating_cost_total = Var(
#         initialize=1e5,
#         domain=NonNegativeReals,
#         doc='Total operating cost [$/year]')
#     b.LCOW = Var(
#         initialize=1e5,
#         domain=NonNegativeReals,
#         doc='Levelized cost of water [$/m3]')
    b.capital_recovery_factor = Var(
         initialize=0.01,
         domain=NonNegativeReals,
         doc='Captial recovery factor')  
#     b.electricity_cost_total = Var(
#         initialize=1e5,
#         domain=NonNegativeReals,
#         doc='Total electricity cost [$/year]')
#     b.other_var_cost_total = Var(
#         initialize=1e5,
#         domain=NonNegativeReals,
#         doc='Other variable cost [$/year]')    
#     b.fixed_op_cost_total = Var(
#         initialize=1e5,
#         domain=NonNegativeReals,
#         doc='Total fixed operating cost [$/year]')
#     b.cat_and_chem_cost_total = Var(
#         initialize=1e5,
#         domain=NonNegativeReals,
#         doc='Catalysts and chemicals cost [$/year]')    
    
    total_capital_investment_var_lst = []
    cat_and_chem_cost_lst = []
    electricity_cost_lst = []
    other_var_cost_lst = []
    total_fixed_op_cost_lst = []
    
    b.capital_recovery_factor.fix(0.08)  
    
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
                #    print(b_unit)
                    recovered_water_flow = recovered_water_flow + b_unit.flow_vol_in[time]

                #if check_waste(b_unit) == "yes":
                #    print(b_unit)    
    b.treated_water = recovered_water_flow
   
    # TODO TOTAL WASTE = 
    ## HERE GET TOTAL ELECTRICITY CONSUMPTION IN KWH AS WELL?
    
    b.LCOW = Expression(
        expr=(b.capital_investment_total * b.capital_recovery_factor + b.operating_cost_annual) 
    / (b.treated_water * 3600 * 24 * 365),
    doc="Levelized Cost of Water in $/m3")
    
    
#    (value(m.fs.costing.capital_investment_total) * value(m.fs.costing.capital_recovery_factor) +
#value(m.fs.costing.operating_cost_total)/20)/((value(m.fs.costing.treated_water) * 3600*24*365/1e6))
    
    
    
    
    
    
    
    