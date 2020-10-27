import numpy as np
import pandas as pd
import datetime
import time
import matplotlib.pyplot as plt
from multiprocessing import Pool
import multiprocessing
import os, sys
from pyomo.environ import *
import pyomo.environ as env

from src import ml_regression
from src import get_graph_chars
from src.financials import *

# media filtration unit process based on Texas Water Development Board IT3PR.
# User Manual ==> https://www.twdb.texas.gov/publications/reports/contracted_reports/doc/1348321632_manual.pdf
# Project Cost for Filter = $725,570 x (flow in mgd) ^ 0.5862 with R2 = 0.996)

# NEEDS TO BE IN MGD FOR THIS UNIT PROCESS
### FLOW IN MUST BE IN M3/DAY OR MGD### TODO
# flow_in = 30;  unit = 'mgd'

### THESE SHOULD BE COMING FROM ELSEWHERE
unit = "m3d"
deep_bed_denitrifying_filter = True

# unit conversion needed for model
if unit == "m3d":
    volume_conversion_factor = 1 / (0.0037854 * 1000000)  # million gallons to m3
else:
    volume_conversion_factor = 1


# NEEDS TO BE IN MGD FOR THIS UNIT PROCESS

#########################################################################
#########################################################################

contact_time = 1.5  # hours
contact_time_mins = 1.5 * 60
ct = 450  # mg/L-min ---> ASSUME CALI STANDARD FOR NOW
chlorine_decay_rate = 3.0  # mg/Lh

# TO DO:
# Chlorine Consumption?
# Trace Organic Chemicals (TOrC)
# Estradiol Equivalency (EEQ)
# Giardia lamblia
# Total Coliforms (including fecal coliform and E. Coli)
# Viruses (enteric)

recovery_factor = 1.0  ## ASSUMED AS 1.0


#### OTHER NEEDED VARIABLES BUT NOT FOR THIS TREATMENT
toc_removal = 0.0  # Asano et al (2007)
nitrate_removal = 0.0
TOrC_removal = 0.25

############################################################
############################################################
############### FUNCTION FOR UP ############################
############################################################

# Perfomance Parameter Values for Process: Constituent removals. If not here, assume 0.
def get_cl2_dem(G):
    # unit is mg/L. order matters in this list. need a better way.

    up_type_list = []
    for i in range(0, len(get_graph_chars.get_unit_process_name_list_for_set_up(G))):
        up_type_list.append(
            get_graph_chars.get_unit_process_name_list_for_set_up(G)[i].split("_")[0]
        )

    if "secondary_BODonly" in up_type_list:
        return 0
    if "secondary_nitrified" in up_type_list:
        return 5
    if "secondary_denitrified" in up_type_list:
        return 5
    if "mbr" in up_type_list:
        return 4
    if "tertiary_media_filtration" in up_type_list:
        return 5
    if "media_filtration" in up_type_list:
        return 5
    if "biologically_active_filtration" in up_type_list:
        return 2
    if "microfiltration" in up_type_list:

        if "cas" in up_type_list:
            return 12
        elif "nas" in up_type_list:
            return 4
        elif "ozonation" in up_type_list:
            return 3
        elif "o3_baf" in up_type_list:
            return 2
        else:
            return 0
    if "ultrafiltration" in up_type_list:

        if "cas" in up_type_list:
            return 12
        elif "nas" in up_type_list:
            return 4
        elif "ozonation" in up_type_list:
            return 3
        elif "o3_baf" in up_type_list:
            return 2
        else:
            return 0
    if "ozonation" in up_type_list:
        return 3
    if "uv" in up_type_list:
        return 0
    if "reverse_osomisis" in up_type_list:
        return 0

    print("assuming initial chlorine demand is 0")

    return 0


#########################################################################
#########################################################################
################# UP COST CALCULATIONS FOR TREATMENT TRAIN ##############
#########################################################################
#########################################################################


def get_chlorine_dose_cost(G, flow_in, dose):

    df = pd.read_csv("data/chlorine_dose_cost_twb.csv") # % dir_path)  # import data

    flow_for_function = flow_in

    max_flow = df.Flow_m3day.max()
    cost_value1 = 0
    flow_list = []
    y_value = "Cost"
    poly_ml, coeff_poly = ml_regression.make_simple_poly(df, y_value)
    # print('applied_cl2_dose' : dose)

    f_array = []
    f1 = dose
    f2 = flow_for_function
    f3 = dose ** 2
    f4 = flow_for_function * dose
    f5 = flow_for_function ** 2
    f6 = dose ** 3
    f7 = flow_for_function * dose ** 2
    f8 = dose * flow_for_function ** 2
    f9 = flow_for_function ** 3
    f_array.append([f1, f2, f3, f4, f5, f6, f7, f8, f9])

    cost_sum = 0
    i = 0
    for co_value in coeff_poly.Coefficients:
        cost_value = co_value * f_array[0][i]
        cost_sum = cost_sum + cost_value
        i = i + 1

    return cost_sum


def total_up_cost(
    m=None, G=None, flow_in=0, cost_method="wt"
):  # ONLY NEEDS FLOW IN FOR NOW

    initial_chlorine_demand = get_cl2_dem(G)
    # print('initial_chlorine_demand:', initial_chlorine_demand, 'mg/L')
    applied_cl2_dose = (
        initial_chlorine_demand
        + chlorine_decay_rate * contact_time
        + ct / contact_time_mins
    )  # mg/L

    # print('applied_cl2_dose:', applied_cl2_dose, 'mg/L')
    ################### TWB METHOD ###########################################################
    if cost_method == "twb":
        return get_chlorine_dose_cost(G, flow_in, applied_cl2_dose) / 1000  # $MM
    ##############################################################################

    ################### WATERTAP METHOD ###########################################################

    flow_in = flow_in * volume_conversion_factor

    # cost index values
    df = get_ind_table()
    cap_replacement_parts = df.loc[basis_year].Capital_Factor
    catalysts_chemicals = df.loc[basis_year].CatChem_Factor
    labor_and_other_fixed = df.loc[basis_year].Labor_Factor
    consumer_price_index = df.loc[basis_year].CPI_Factor

    # capital costs (unit: MM$) ---> TCI IN EXCEL ___> EQUATION BELOW IS IMPORTANT!!
    fixed_cap_inv_unadjusted = (
        get_chlorine_dose_cost(G, flow_in, applied_cl2_dose) / 1000
    )  # $MM
    fixed_cap_inv = fixed_cap_inv_unadjusted * cap_replacement_parts
    land_cost = fixed_cap_inv * land_cost_precent_FCI
    working_cap = fixed_cap_inv * working_cap_precent_FCI
    total_cap_investment = fixed_cap_inv + land_cost + working_cap

    #### ASUMPTION MIKE CHECK ####
    base_fixed_cap_cost = fixed_cap_inv_unadjusted

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


def tds_treatment_equation(m, G, link_variable_wname, up_edge):
    return link_variable_wname * 1


#########################################################################
#########################################################################
################# UP CONSTITUENT CALCULATIONS ###########################
#########################################################################
#########################################################################


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
