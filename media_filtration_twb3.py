import numpy as np
import pandas as pd
import datetime
import time
import matplotlib.pyplot as plt
from multiprocessing import Pool
import multiprocessing
import os, sys

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
toc_removal = 0.2 # Asano et al (2007)
if deep_bed_denitrifying_filter == True:
    nitrate_removal = 0.8 #Mohseni-Bandpi et al., 2013
    TOrC_removal = 0.2 # Reungoat et al. (2009) and Falas et al. (2016)
    EEQ_removal = 0.2 # Reungoat et al. (2009) and Falas et al. (2016)

# captial costs basis
#Project Cost for Filter = $725,570 x (flow in mgd) 0.5862 with R2 = 0.996 (page 55)
# note: says not to extrapolate beyond 30 MGD but we do if needed.
base_fixed_cap_cost = 0.725570 #from TWB
cap_scaling_exp = 0.586 #from TWB

recovery_factor = 0.85 ## ASSUMED AS 1.0 -> MUST BE WRONG -> CHECK


#########################################################################
#########################################################################
################# UP COST CALCULATIONS FOR TREATMENT TRAIN ##############
#########################################################################
#########################################################################

def total_up_cost(m = None, G = None, flow_in = 0, deep_bed_denitrifying_filter = True): # ONLY NEEDS FLOW IN FOR NOW
    
    flow_in = flow_in * volume_conversion_factor 
    print('flow_in mgd:', flow_in)
    
    # cost index values
    df = pd.read_csv('plant_cost_indices.csv')
    df = get_ind_table(df)
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
    print('edge', edge)
    G.edges[edge]['recovery_factor'] = recovery_factor
    
    #G.nodes[unit_process_name]['recovery_factor'] = recovery_factor
    
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
        print('no water flow to recycle')
    
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