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
    Expression, Var, Param, NonNegativeReals, units as pyunits)


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
    

# This first method is used at the flowsheet level and contains any global
# parameters and methods
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
def _make_vars(self):
    # build generic costing variables (all costing models need these vars)
    self.base_cost = Var(initialize=1e5,
                         domain=NonNegativeReals,
                         doc='Unit Base Cost cost in $')
    self.purchase_cost = Var(initialize=1e4,
                             domain=NonNegativeReals,
                             doc='Unit Purchase Cost in $')



    
    