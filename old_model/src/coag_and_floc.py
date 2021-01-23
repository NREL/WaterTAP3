import numpy as np
import pandas as pd
import datetime
import time
import matplotlib.pyplot as plt
from multiprocessing import Pool
import multiprocessing
import os, sys

from src.financials import *

# Adapted from Jenny's excel "Coagulation and Flocculation with Aluminmum Sulfate" version in WaterTAP3 VAR tab
# Sources: https://www.mrwa.com/WaterWorksMnl/Chapter%2012%20Coagulation.pdf
# Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura)
# https://www.iwapublishing.com/news/coagulation-and-flocculation-water-and-wastewater-treatment

# NEEDS TO BE IN MGD FOR THIS UNIT PROCESS
### FLOW IN MUST BE IN GPM### 

### THESE SHOULD BE COMING FROM ELSEWHERE --> TODO WHAT IS HAPPENING WITH UNITS. UNITS AND CONVERSIONS MUST BE DEFINED.
#unit = "GPM"

# unit conversion needed for model
#if unit == "m3h":
#    volume_conversion_factor = 1 * 4.402868  # m3/hr to GPM
#else:
#    volume_conversion_factor = 1

#########################################################################
#########################################################################
#########################################################################

# Coagulation and Flocculation (High G) with Aluminum Sulfate
#flow_in = 55368 # GPM base volumetric flow (55368 GPM = 12575 m3/hr)
x = "TPEC" # changeable by user. What is this?????
TPEC = 3.4
TIC = 1.65
rapid_mixers = 1
floc_mixers = 3
rapid_mix_processes = 1
floc_processes = 1
coag_processes = 1
poly_dosage = .1 # mg/L dosage rate
rapid_retention_time = 10 # seconds (rapid mix)
floc_retention_time =  12 # minutes
al2so43_density = 8.34 * 1.33 # lb/gal
al2so43_dosage = 10 # mg/L dosage rate

inlet_TOC = 7 # (mg/L) user input or link to inlet water quality parameter TODO->what is this for!
inlet_alkalinity = 60 # (mg/L as CaCO3) user input or link to inlet water quality parameter
inlet_uva = 0 # cm^-1 user input or link to inlet water quality parameter
inlet_turbidity = 11 # NTU user input or link to inlet water quality parameter
SUVA = 3 # (L/(mg*m)) SUVA = UVA/DOC*100
toc_removal = .45 # output to watertap3 (please use table of TOC removal in excel WaterTAP3)
turbidity = 2 # NTU output to watertap3


recovery_factor = 1 #TODO
nitrate_removal = 1 #TODO
TOrC_removal = 1 #TODO
toc_removal = 1 #TODO
EEQ_removal = 1 #TODO
cap_scaling_exp = 1 # TODO SHOW



def capital_costs(TIC, TPEC, flow_in):
    rapid_basin_volume = rapid_retention_time/60 * flow_in # gallons #TODO THIS SHOULD BE IN A FUNCTION # SHOULD THIS SAY MIX?!?!?
    floc_basin_volume = floc_retention_time * flow_in # gallons #TODO THIS SHOULD BE IN A FUNCTION
    al2so43_dosage_lb_per_hour = al2so43_dosage * .00050073 * flow_in #TODO THIS SHOULD BE IN A FUNCTION
    poly_dosage_lb_per_hour = poly_dosage * .00050073 * flow_in #TODO THIS SHOULD BE IN A FUNCTION
    
    rapid_G = (7.0814 * rapid_basin_volume + 33269) * rapid_mix_processes # $
    floc_G = (952902 * floc_basin_volume/1000000 + 177335) * floc_processes # $
    coag_injection = (212.32 * al2so43_dosage_lb_per_hour + 73225) * coag_processes # $
    floc_injection = (13662 * poly_dosage_lb_per_hour * 24 + 20861) * floc_processes # flow_in comes in as GPM but needs to be in m3/hr
    
    total_cap_costs = rapid_G + floc_G + coag_injection + floc_injection
    
    return total_cap_costs

def fixed_cap_investment(TIC, TPEC, flow_in): #TODO
    if x == "TPEC":
        TPEC = TIC
    else:
        TPEC = 1
    
    if x == "TIC":
        TIC = TIC
    else:
        TIC = 1

    fixed_cap = capital_costs(TIC, TPEC, flow_in) * TPEC * TIC # $
    
    return fixed_cap

def total_power_consumption(flow_in):
    
    power_consumption = 80**2 * .001 * floc_basin_volume/264.172
    floc_mix_power = power_consumption * floc_mixers    
    
    power_consumption = 900**2 * .001 * rapid_basin_volume/264.172
    rapid_mix_power = power_consumption * rapid_mixers
    
    total_power = rapid_mix_power + floc_mix_power
    total_power_per_m3 = (total_power/1000) / (flow_in / 4.402868)
    
    return total_power_per_m3 # kWh/m3




#########################################################################
#########################################################################
################# UP COST CALCULATIONS FOR TREATMENT TRAIN ##############
#########################################################################
#########################################################################


def total_up_cost(
    m=None, G=None, flow_in=0, cost_method="wt"
):  # ONLY NEEDS FLOW IN FOR NOW
    volume_conversion_factor = 1/24 # THIS IS BECAUSE ITS BASED ON M3/HR
    flow_in = flow_in * volume_conversion_factor

    ################### MRWA METHOD ###########################################################
    if cost_method == "MRWA": # TODO
        return fixed_cap_investment(TIC, TPEC, flow_in) # TO DO SHOULD LOOK LIKE THIS? FUNCTION OF FLOW ! base_fixed_cap_cost * flow_in ** cap_scaling_exp
    ##############################################################################

    ################### WATERTAP METHOD ###########################################################
    # cost index values
    
    base_fixed_cap_cost = fixed_cap_investment(TIC, TPEC) / 1000000
   
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