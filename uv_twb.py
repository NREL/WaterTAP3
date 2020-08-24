import numpy as np
import pandas as pd
import datetime
import time
import matplotlib.pyplot as plt
from multiprocessing import Pool
import multiprocessing
import os, sys
from pyomo.environ import *

import ml_regression

# media filtration unit process based on Texas Water Development Board IT3PR. 
# User Manual ==> https://www.twdb.texas.gov/publications/reports/contracted_reports/doc/1348321632_manual.pdf
#Project Cost for Filter = $725,570 x (flow in mgd) ^ 0.5862 with R2 = 0.996)

# NEEDS TO BE IN MGD FOR THIS UNIT PROCESS
### FLOW IN MUST BE IN M3/DAY OR MGD### TODO
#flow_in = 30;  unit = 'mgd'

### THESE SHOULD BE COMING FROM ELSEWHERE
unit = 'm3d'
deep_bed_denitrifying_filter = True

#unit conversion needed for model
if unit == 'm3d':
    volume_conversion_factor = 1 / (0.0037854 * 1000000) # million gallons to m3
else:
    volume_conversion_factor = 1

    
# NEEDS TO BE IN MGD FOR THIS UNIT PROCESS
    
############################################################
############################################################
############### FUNCTION FOR UP ############################
############################################################

def get_ind_table(df):

    df1 = pd.DataFrame()
    for name in df.columns[1:]:
        a, b = get_linear_regression(list(df.Year), list(df[('%s' % name)]), name)
        new_list = []; yr_list = [];
        for yr in range(df.Year.max()+1, last_year_for_cost_indicies+1):
            new_list.append(a*yr + b)
            yr_list.append(yr)
        df1[name] = new_list
    df1['Year'] = yr_list
    df = pd.concat([df, df1], axis = 0)

    new_cost_variables = ['Capital', 'CatChem', 'Labor', 'CPI']
    for variable in new_cost_variables:
        ind_name = ('%s_Index' % variable)
        fac_name = ('%s_Factor' % variable)
        df[fac_name] = df[ind_name] / df[df.Year == analysis_yr_cost_indicies][ind_name].max()
    
    df = df.set_index(df.Year)
    
    return df


def get_linear_regression(x_values, y_values, variable):
    #print('nonlinear did not work, trying linear for:', variable)
    
    from sklearn.linear_model import LinearRegression
    X = np.array(x_values).reshape(-1, 1)
    y = np.array(y_values).reshape(-1, 1)
    reg = LinearRegression().fit(X, y)
    #print('linear score for:', variable, reg.score(X, y))
    
    #a_list=[0] -> NOT SURE WHY THIS WAS HERE
    a=reg.coef_[0]
    b=reg.intercept_
    #threshold_temp=[0]

    return a[0], b[0]

#########################################################################
#########################################################################
### USER INPUTS: FINANCIAL INFORMATION -> GLOBAL FOR ENTIRE TRAIN #######
#########################################################################

fixed_op_cost_scaling_exp = 0.7 # source:
basis_year = 2014 # meaning:
analysis_yr_cost_indicies = 2025
last_year_for_cost_indicies = 2050
on_stream_factor = 0.95

salaries_percent_FCI = 0.01 #represented as a fraction. source:
land_cost_precent_FCI = 0.0015 #represented as a fraction. source:
working_cap_precent_FCI = 0.05 #represented as a fraction. source:
maintinance_costs_precent_FCI =  0.03
lab_fees_precent_FCI = 0.01
insurance_taxes_precent_FCI = 0.007

benefit_percent_of_salary = 0.9

elec_price = 0.01


############################################################

# Perfomance Parameter Values for Process: Constituent removals. If not here, assume 0.

# TO DO:
#Trace Organic Chemicals (TOrC)
#Estradiol Equivalency (EEQ)
#Giardia lamblia
#Total Coliforms (including fecal coliform and E. Coli)
#Viruses (enteric)

recovery_factor = 1.0 ## ASSUMED AS 1.0

# CALCULATED feed_uvt = 0.75 ## CHANGES BASED ON OTHER PARAMS IN TRAIN. 0.6 OTHERWISE.
dose = 600 ## BASED ON TABLE 3.15 and 3.16 --> SHOULD BE BASED ON REMOVAL REQUEST CONSTIUENT
TOrC_removal = 0.25 # BASED ON DOSE

#### OTHER NEEDED VARIABLES BUT NOT FOR THIS TREATMENT
toc_removal = 0.0 # Asano et al (2007)
nitrate_removal = 0.0

#########################################################################
#########################################################################
################# UP COST CALCULATIONS FOR TREATMENT TRAIN ##############
#########################################################################
#########################################################################
################# GET UVT FEED ##########################################

def get_uvt_feed(G):
    
    import watertap as wt
        
    up_type_list = [] 
    for i in range(0, len(wt.get_graph_chars.get_unit_process_name_list_for_set_up(G))):
        up_type_list.append(wt.get_graph_chars.get_unit_process_name_list_for_set_up(G)[i].split('_')[0])
    
    if 'secondary_BODonly' in up_type_list:
        return 0.6
    if 'secondary_nitrified' in up_type_list:
        return 0.7
    if 'secondary_denitrified' in up_type_list:
        return 0.7
    if 'mbr' in up_type_list:
        return 0.7
    if 'tertiary_media_filtration' in up_type_list:
        return 0.65 
    if 'media_filtration' in up_type_list:
        return 0.65 ## same as tertiary
    if 'biologically_active_filtration' in up_type_list:
        return 0.85 
    if 'microfiltration' in up_type_list:
        return 0.7 ## assumes mid range. could be better.
    if 'ultrafiltration' in up_type_list:
        return 0.7 ## assumes mid range. could be better.
    if 'ozonation' in up_type_list:
        return 0
    if 'ro' in up_type_list:
        return 0.95
    
    print('assuming uvt feed is 60%')
    
    return 0.6 # assumes minimum from range otherwise.


#########################################################################
##################### COST #############################################


def get_uv_cost(G, flow_in, dose):
    # dose in Mj/cm2, feed uvt in %, cost in $MM
    
    import pyomo.environ as env
    
    feed_uvt = 0.7 #get_uvt_feed(G)
    #dose = get_dose() TO DO! 
    
    #print('feed_uvt:', feed_uvt)
    
    dir_path = '/Users/amiara/NAWI/WaterTap/Python_UPlinks'
    df = pd.read_csv('%s/uv_cost_twb.csv' % dir_path) #import data
    
    flow_for_function = flow_in / 1000000 # converted to millions for regression
    
    y_value = 'Cost'
    
    if feed_uvt < 0.55: print('error: UVT feed assumed to be at least 55%')
    
    if ((feed_uvt >= 0.55) & (feed_uvt < 0.60)): df = df[df.FeedUVT == 0.55]

    if ((feed_uvt >= 0.60) & (feed_uvt < 0.65)): df = df[df.FeedUVT == 0.60]
    
    if ((feed_uvt >= 0.65) & (feed_uvt < 0.70)): df = df[df.FeedUVT == 0.65]
        
    if ((feed_uvt >= 0.70) & (feed_uvt < 0.75)): df = df[df.FeedUVT == 0.70]
        
    if ((feed_uvt >= 0.75) & (feed_uvt < 0.85)): df = df[df.FeedUVT == 0.75]
    
    if ((feed_uvt >= 0.85) & (feed_uvt < 0.90)): df = df[df.FeedUVT == 0.85]
        
    if ((feed_uvt >= 0.90) & (feed_uvt < 0.95)): df = df[df.FeedUVT == 0.90]
        
    if ((feed_uvt >= 0.95) & (feed_uvt < 1.00)): df = df[df.FeedUVT == 0.95]        
        
    df = df.reset_index()
    del df['FeedUVT']; del df['index']
    
    poly_ml, coeff_poly = ml_regression.make_simple_poly(df, y_value) 
    
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
    co_values = []
    i = 0 
    for co_value in coeff_poly.Coefficients:
            cost_value = co_value * f_array[0][i]
            cost_sum = cost_sum + cost_value
            i = i + 1
    
    return cost_sum



def total_up_cost(m = None, G = None, flow_in = 0, cost_method = 'wt'): # ONLY NEEDS FLOW IN FOR NOW
    
    
    feed_uvt = get_uvt_feed(G)
   
    ################### TWB METHOD ###########################################################
    if cost_method == 'twb': return get_uv_cost(G, flow_in, dose) #$MM
    ##############################################################################
  
    ################### WATERTAP METHOD ###########################################################    
    
    flow_in = flow_in * volume_conversion_factor 
    
    # cost index values
    df = pd.read_csv('plant_cost_indices.csv')
    df = get_ind_table(df)
    cap_replacement_parts = df.loc[basis_year].Capital_Factor
    catalysts_chemicals = df.loc[basis_year].CatChem_Factor
    labor_and_other_fixed = df.loc[basis_year].Labor_Factor
    consumer_price_index = df.loc[basis_year].CPI_Factor

    # capital costs (unit: MM$) ---> TCI IN EXCEL ___> EQUATION BELOW IS IMPORTANT!!
    fixed_cap_inv_unadjusted = get_uv_cost(G, flow_in, dose) #$MM
    fixed_cap_inv = fixed_cap_inv_unadjusted * cap_replacement_parts
    land_cost = fixed_cap_inv * land_cost_precent_FCI
    working_cap = fixed_cap_inv * working_cap_precent_FCI
    total_cap_investment = fixed_cap_inv + land_cost + working_cap

    
    #### ASUMPTION MIKE CHECK ####
    base_fixed_cap_cost = fixed_cap_inv_unadjusted
    
    # variable operating costs (unit: MM$/yr) -> MIKE TO DO -> ---> CAT+CHEM IN EXCEL
    # --> should be functions of what is needed!?
    #cat_chem_df = pd.read_csv('catalyst_chemicals.csv')
    #cat_and_chem = flow_in * 365 * on_stream_factor # TODO
    electricity = 0 #flow_in * 365 * on_stream_factor * elec_price # TODO
    cat_and_chem_cost = 0 # TODO
    electricity_cost = electricity * elec_price * 365 # KWh/day * $/KWh * 365 days
    other_var_cost = cat_and_chem_cost - electricity_cost


    # fixed operating cost (unit: MM$/yr)  ---> FIXED IN EXCEL
    base_employee_salary_cost = base_fixed_cap_cost * salaries_percent_FCI
    salaries = labor_and_other_fixed * base_employee_salary_cost * flow_in ** fixed_op_cost_scaling_exp
    benefits = salaries * benefit_percent_of_salary
    maintenance = maintinance_costs_precent_FCI * fixed_cap_inv
    lab = lab_fees_precent_FCI * fixed_cap_inv
    insurance_taxes = insurance_taxes_precent_FCI * fixed_cap_inv
    total_fixed_op_cost = salaries + benefits + maintenance + lab + insurance_taxes
    
    total_up_cost = total_cap_investment +  cat_and_chem_cost +  electricity_cost + other_var_cost + total_fixed_op_cost 
        
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

#########################################################################
#########################################################################
################# UP CONSTITUENT CALCULATIONS ###########################
#########################################################################
#########################################################################




#### ADDING ATTRIBUTES ---> NEEDS TO BE ONE ENTIRE FUNCTION WITH SUB FUNCTIONS #####

BOD_constraint = 250
TOC_constraint = 150

def get_edge_info(unit_process_name):
    start_node = ('%s_start' % unit_process_name)
    end_node = ('%s_end' % unit_process_name)
    edge = (start_node, end_node)
    return start_node, end_node, edge

def add_recovery_attribute(G, unit_process, unit_process_name):
    
    start_node, end_node, edge = get_edge_info(unit_process_name)
    G.edges[edge]['recovery_factor'] = recovery_factor
        
    return G

def add_BOD_inlet_constraint(G, unit_process, unit_process_name):
    start_node, end_node, edge = get_edge_info(unit_process_name)
    G.edges[edge]['BOD_constraint'] = BOD_constraint
    return G

def add_TOC_inlet_constraint(G, unit_process, unit_process_name):
    start_node, end_node, edge = get_edge_info(unit_process_name)
    G.edges[edge]['TOC_constraint'] = TOC_constraint
    return G

def add_recycle_and_waste_attribute(G, unit_process, unit_process_name, recyle_fraction_of_waste=None):
    
    start_node, end_node, edge = get_edge_info(unit_process_name)
    if recovery_factor == 1:  
        recyle_fraction_of_waste = 0
    
    if recyle_fraction_of_waste is None: 
        G.edges[edge]['recycle_factor'] = 0
        G.edges[edge]['waste_factor'] = 1 - recovery_factor
    else:
        G.edges[edge]['recycle_factor'] = (1 - recovery_factor) * (recyle_fraction_of_waste)
        G.edges[edge]['waste_factor'] = 1 - recovery_factor - G.edges[edge]['recycle_factor']
    
    return G

def main():
    print("importing something")
    # need to define anything here?

if __name__ == "__main__":
    main()