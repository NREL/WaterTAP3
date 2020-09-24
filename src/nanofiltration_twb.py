import numpy as np
import pandas as pd
import datetime
import time
import matplotlib.pyplot as plt
from multiprocessing import Pool
import multiprocessing
import os, sys

from src.financials import *

# microfiltration unit process based on Texas Water Development Board IT3PR.
# User Manual ==> https://www.twdb.texas.gov/publications/reports/contracted_reports/doc/1348321632_manual.pdf

# NEEDS TO BE IN MGD FOR THIS UNIT PROCESS
### FLOW IN MUST BE IN M3/DAY OR MGD### TODO
# flow_in = 30;  unit = 'mgd'

### THESE SHOULD BE COMING FROM ELSEWHERE
unit = "m3d"

# unit conversion needed for model
if unit == "m3d":
    volume_conversion_factor = 1 / (0.0037854 * 1000000)  # million gallons to m3
else:
    volume_conversion_factor = 1


# NEEDS TO BE IN MGD FOR THIS UNIT PROCESS
############################################################

# Perfomance Parameter Values for Process: Constituent removals.
toc_removal = 0.93  # Asano et al (2007)
nitrate_removal = 0.25  # Asano et al (2007)
TOrC_removal = 0.75  # Schäfer et al., 2005
EEQ_removal = 0.75  # Racz and Goel, 2010
ndma_removal = 0.05  # Steinle-Darling et al., 2007, Plumlee et al., 2008
pfos_pfoa_removal = 0.90  # Removal due to relative size of PFOS and PFOA, Tang(2006)


# captial costs basis
base_fixed_cap_cost = 3.75  # from TWB
cap_scaling_exp = 1  # from TWB
recovery_factor = 0.8  ##


#########################################################################
#########################################################################
################# UP COST CALCULATIONS FOR TREATMENT TRAIN ##############
#########################################################################
#########################################################################


def total_up_cost(
    m=None, G=None, flow_in=0, cost_method="wt"
):  # ONLY NEEDS FLOW IN FOR NOW

    flow_in = flow_in * volume_conversion_factor
    # print('flow_in mgd:', flow_in)

    ################### TWB METHOD ###########################################################
    if cost_method == "twb":
        return base_fixed_cap_cost * flow_in ** cap_scaling_exp
    ##############################################################################

    ################### WATERTAP METHOD ###########################################################
    # cost index values
    df = get_ind_table()
    cap_replacement_parts = df.loc[basis_year].Capital_Factor
    catalysts_chemicals = df.loc[basis_year].CatChem_Factor
    labor_and_other_fixed = df.loc[basis_year].Labor_Factor
    consumer_price_index = df.loc[basis_year].CPI_Factor

    # capital costs (unit: MM$) ---> TCI IN EXCEL
    fixed_cap_inv_unadjusted = base_fixed_cap_cost * flow_in ** cap_scaling_exp
    fixed_cap_inv = fixed_cap_inv_unadjusted * cap_replacement_parts
    land_cost = fixed_cap_inv * land_cost_precent_FCI
    working_cap = fixed_cap_inv * working_cap_precent_FCI
    total_cap_investment = fixed_cap_inv + land_cost + working_cap

    # variable operating costs (unit: MM$/yr) -> MIKE TO DO -> ---> CAT+CHEM IN EXCEL
    # --> should be functions of what is needed!?
    # cat_chem_df = pd.read_csv('catalyst_chemicals.csv')
    # cat_and_chem = flow_in * 365 * on_stream_factor # TODO
    electricity = 0  # flow_in * 365 * on_stream_factor * elec_price # TODO
    cat_and_chem_cost = 0  # TODO
    electricity_cost = electricity * elec_price * 365  # KWh/day * $/KWh * 365 days
    other_var_cost = cat_and_chem_cost - electricity_cost

    # fixed operating cost (unit: MM$/yr)  ---> FIXED IN EXCEL
    base_employee_salary_cost = base_fixed_cap_cost * salaries_percent_FCI
    salaries = (
        labor_and_other_fixed
        * base_employee_salary_cost
        * flow_in ** fixed_op_cost_scaling_exp
    )
    benefits = salaries * benefit_percent_of_salary
    maintenance = maintinance_costs_precent_FCI * fixed_cap_inv
    lab = lab_fees_precent_FCI * fixed_cap_inv
    insurance_taxes = insurance_taxes_precent_FCI * fixed_cap_inv
    total_fixed_op_cost = salaries + benefits + maintenance + lab + insurance_taxes

    total_up_cost = (
        total_cap_investment
        + cat_and_chem_cost
        + electricity_cost
        + other_var_cost
        + total_fixed_op_cost
    )

    return total_up_cost


def flow_treatment_equation(m, G, link_variable):
    return link_variable * recovery_factor


def toc_treatment_equation(m, G, link_variable):
    return link_variable * (1 - toc_removal)


def nitrate_treatment_equation(m, G, link_variable):
    return link_variable * (1 - nitrate_removal)


def eeq_treatment_equation(m, G, link_variable):
    return link_variable * (1 - EEQ_removal)


def torc_treatment_equation(m, G, link_variable):
    return link_variable * (1 - TOrC_removal)


#### ADDING ATTRIBUTES ---> NEEDS TO BE ONE ENTIRE FUNCTION WITH SUB FUNCTIONS #####


def get_edge_info(unit_process_name):
    start_node = "%s_start" % unit_process_name
    end_node = "%s_end" % unit_process_name
    edge = (start_node, end_node)
    return start_node, end_node, edge


def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()
