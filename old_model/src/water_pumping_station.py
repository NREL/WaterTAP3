import numpy as np
import pandas as pd
import datetime
import time
import matplotlib.pyplot as plt
from multiprocessing import Pool
import multiprocessing
import os, sys

from src.financials import *

# Water pumping station power demands
# Adapted from Jenny's excel "Water Pumping Station" version in WaterTAP3 VAR tab
# Sources: https://www.engineeringtoolbox.com/water-pumping-costs-d_1527.html
# https://onlinelibrary.wiley.com/doi/pdf/10.1002/9780470260036.ch5
# Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura)

# NEEDS TO BE IN MGD FOR THIS UNIT PROCESS
### FLOW IN MUST BE IN M3/DAY OR MGD### TODO
# flow_in = 30;  unit = 'mgd'

### THESE SHOULD BE COMING FROM ELSEWHERE
#unit = "MGD"

# unit conversion needed for model
#if unit == "m3h":
#    volume_conversion_factor = 1 / 158  # m3/hr to MGD
#else:
#    volume_conversion_factor = 1


    

### THESE SHOULD BE COMING FROM ELSEWHERE
unit = "m3d"

# unit conversion needed for model
if unit == "m3d":
    volume_conversion_factor = 1 / (0.0037854 * 1000000)  # million gallons to m3
else:
    volume_conversion_factor = 1    
    
    
#########################################################################
#########################################################################
#########################################################################
pump_station = "Raw Water"

x = "TPEC" # changeable by user
TPEC = 3.4
TIC = 1.65

# pump parameters
life_height = 30 # ft
pump_efficiency = .9
motor_efficiency = .9



def fixed_cap2(flow_in, TPEC, TIC):

    if pump_station == "Raw Water":
        
        cap_cost = 12169 * flow_in + 60716

        if x != "TPEC": TPEC = 1

        if x != "TIC": TIC = 1

        return cap_cost * TPEC * TIC # $

    else:  # pump_station = "Treated Water":
        cap_cost = 57887 * flow_in ** 0.7852
        
        if x != "TPEC": TPEC = 1

        if x != "TIC": TIC = 1

        return cap_cost * TPEC * TIC # $

def fixed_cap(flow_in):
    
    return 57887 * flow_in ** 0.7852
    #return 12169 * flow_in + 60716 

def pumping_power(flow_in):
    pumping_power = .746 * (flow_in * 695.2) * life_height/(3960 * pump_efficiency * motor_efficiency)/ (flow_in * 158)
    
    return pumping_power
    

#########################################################################
#########################################################################
################# UP COST CALCULATIONS FOR TREATMENT TRAIN ##############
#########################################################################
#########################################################################


#########################################################################
#########################################################################
#########################################################################

# Perfomance Parameter Values for Process: Constituent removals.
toc_removal = 0.0  # Asano et al (2007)
nitrate_removal = 0.0  # None but in Excel tool appears to be removed sometimes?
TOrC_removal = 0.0  # slightly lower removal than for UF. Some removal is expected due to particle association of TOrCs.
EEQ_removal = 0.0  # Linden et al., 2012 (based on limited data))
NDMA_removal = 0.0
PFOS_PFOA_removal = 0.0
protozoa_removal = 0.0
virus_removal = 0.0

# captial costs basis
# Project Cost for Filter = $2.5M x (flow in mgd) page 55)
base_fixed_cap_cost = 57887  # from TWB -> THIS IS SOMEHOW DIFFERENT FROM EXCEL CALCS NOT SURE WHY (3.125))

cap_scaling_exp = 0.7852  # from TWB

recovery_factor = 1.0  ## ASSUMED AS 1.0 -> MUST BE WRONG -> CHECK


# recycle_factor = (1 - recovery_factor) * (recyle_fraction_of_waste)
waste_factor = 1 - recovery_factor  # - G.edges[edge]['recycle_factor']

#########################################################################
#########################################################################
################# UP COST CALCULATIONS FOR TREATMENT TRAIN ##############
#########################################################################
#########################################################################


def total_up_cost(
    m=None, G=None, flow_in=0, cost_method="wt"
):  # ONLY NEEDS FLOW IN FOR NOW

    flow_in = flow_in * volume_conversion_factor

    ################### TWB METHOD ###########################################################
    #if cost_method == "twb":
    #    return base_fixed_cap_cost * flow_in ** cap_scaling_exp
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


#####################################################################
#####################################################################


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


#####################################################################
#####################################################################
#### NETWORK RELATED FUNCTIONS AND DATA #####


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