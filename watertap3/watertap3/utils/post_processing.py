import os

from pylab import *
import pandas as pd
import numpy as np
from pyomo.environ import Block, value

# from ..watertap3 import case_study_trains
from . import generate_constituent_list
#global scenario
#global case_study

__all__ = ['get_results_table',
           'combine_case_study_results',
           'compare_with_excel']

up_variables = [
    "fixed_cap_inv",
    "land_cost",
    "working_cap",
    "total_cap_investment",
    "cat_and_chem_cost",
    "electricity_cost",
    "other_var_cost",
    "salaries",
    "benefits",
    "maintenance",
    "lab",
    "insurance_taxes",
    "total_fixed_op_cost",
    "base_employee_salary_cost",
    "electricity_cost",
    "annual_op_main_cost"]

def get_results_table(m = None, scenario = None, case_study = None, save = True):
    # could make a dictionary if betteR?
    #unit_process_names = case_study_trains.get_unit_processes(case_study_trains.case_study, 
    #                                                         case_study_trains.scenario)
    
    if scenario is None:
        scenario = case_study_trains.train["scenario"]
    if case_study is None:
        case_study = case_study_trains.train["case_study"]

    up_name_list = []
    variable_list = []
    value_list = []
    category = []
    unit_list = []

    name_lup = pd.read_csv("data/excel_to_python_names.csv", index_col="Python_variable")

    for b_unit in m.fs.component_objects(Block, descend_into=False):
        if hasattr(b_unit, 'electricity'):
            up_name_list.append(str(b_unit)[3:])
            variable_list.append("Electricity Intensity Unit Inlet")
            value_list.append(value(getattr(b_unit, "electricity")))
            unit_list.append("kwh/m3")
            category.append("Electricity")
        
        if hasattr(b_unit, 'elec_int_treated'):
            up_name_list.append(str(b_unit)[3:])
            variable_list.append("Electricity Intensity System Treated")
            value_list.append(value(b_unit.elec_int_treated))
            unit_list.append("kwh/m3")
            category.append("Electricity")
                        
        if hasattr(b_unit, 'costing'):
            if hasattr(b_unit, 'LCOW'):
                up_name_list.append(str(b_unit)[3:])
                category.append("LCOW")
                variable_list.append("Unit Levelized Cost")
                value_list.append(value(b_unit.LCOW))
                unit_list.append("$/m3")  
            
            for variable in up_variables:
                up_name_list.append(str(b_unit)[3:])
                
                if variable == "annual_op_main_cost":
                    variable_list.append("Annual O&M Costs")
                    value_list.append(value(getattr(b_unit.costing, variable)))
                    unit_list.append("$MM/yr")            
                else:
                    variable_list.append(name_lup.loc[variable].Excel_variable)
                    value_list.append(value(getattr(b_unit.costing, variable)))
                    unit_list.append(name_lup.loc[variable].Unit)
                if variable == "electricity":
                    category.append("Electricity")
                else:
                    category.append("Cost")

            value_list.append((value(getattr(m.fs, str(b_unit)[3:]).flow_vol_in[0])))
            up_name_list.append(str(b_unit)[3:])
            variable_list.append("Inlet Water")
            category.append("Water Flow")
            unit_list.append("m3/s")

            value_list.append((value(getattr(m.fs, str(b_unit)[3:]).flow_vol_out[0])))
            up_name_list.append(str(b_unit)[3:])
            variable_list.append("Outlet Water")
            category.append("Water Flow")
            unit_list.append("m3/s")

            value_list.append(value(getattr(m.fs, str(b_unit)[3:]).flow_vol_waste[0]))
            up_name_list.append(str(b_unit)[3:])
            variable_list.append("Waste Water")
            category.append("Water Flow")
            unit_list.append("m3/s")

            for conc in generate_constituent_list.run(m.fs):
                ### MASS IN KG PER M3
                value_list.append(value(getattr(m.fs, str(b_unit)[3:]).conc_mass_in[0, conc]))
                up_name_list.append(str(b_unit)[3:])
                category.append("Inlet Constituent Density")
                variable_list.append(conc)
                unit_list.append("kg/m3")

                value_list.append(value(getattr(m.fs, str(b_unit)[3:]).conc_mass_out[0, conc]))
                up_name_list.append(str(b_unit)[3:])
                category.append("Outlet Constituent Density")
                variable_list.append(conc)
                unit_list.append("kg/m3")

                value_list.append(value(getattr(m.fs, str(b_unit)[3:]).conc_mass_waste[0, conc]))
                up_name_list.append(str(b_unit)[3:])
                category.append("Waste Constituent Density")
                variable_list.append(conc)
                unit_list.append("kg/m3")

                ### MASS IN KG --> MULTIPLIED BY FLOW
                value_list.append(value(getattr(m.fs, str(b_unit)[3:]).conc_mass_in[0, conc])*
                                 value(getattr(m.fs, str(b_unit)[3:]).flow_vol_in[0]))
                up_name_list.append(str(b_unit)[3:])
                category.append("Inlet Constituent Total Mass")
                variable_list.append(conc)
                unit_list.append("kg")

                value_list.append(value(getattr(m.fs, str(b_unit)[3:]).conc_mass_out[0, conc])*
                                 value(getattr(m.fs, str(b_unit)[3:]).flow_vol_out[0]))
                up_name_list.append(str(b_unit)[3:])
                category.append("Outlet Constituent Total Mass")
                variable_list.append(conc)
                unit_list.append("kg")

                value_list.append(
                    value(getattr(m.fs, str(b_unit)[3:]).conc_mass_waste[0, conc]) * 
                                value(getattr(m.fs, str(b_unit)[3:]).flow_vol_waste[0]))
                up_name_list.append(str(b_unit)[3:])
                category.append("Waste Constituent Total Mass")
                variable_list.append(conc)
                unit_list.append("kg")            

    for variable in m.fs.costing.component_objects():
        if "CE_index" in str(variable):
            continue
        elif "capital_recovery_factor" in str(variable):
            continue
        elif "electricity_intensity" in str(variable):
            value_list.append(value(getattr(m.fs.costing, variable_str)))
            up_name_list.append("System")
            category.append("Electricity")
            variable_list.append("Electricity Intensity System Treated")
            unit_list.append("kwh/m3")
        elif "elec_frac_LCOW" in str(variable):
            value_list.append(value(getattr(m.fs.costing, variable_str)))
            up_name_list.append("System")
            category.append("Electricity")
            variable_list.append("Electricity Fraction of LCOW")
            unit_list.append("$/m3")
        elif "LCOW_TCI" in str(variable):
            value_list.append(value(m.fs.costing.LCOW_TCI))
            up_name_list.append("System")
            category.append("LCOW")
            variable_list.append("TCI LCOW")
            unit_list.append("$/m3")            
        elif "LCOW_elec" in str(variable):
            value_list.append(value(m.fs.costing.LCOW_elec))
            up_name_list.append("System")
            category.append("LCOW")
            variable_list.append("Electricity LCOW")
            unit_list.append("$/m3")            
        elif "LCOW_fixed_op" in str(variable):
            value_list.append(value(m.fs.costing.LCOW_fixed_op))
            up_name_list.append("System")
            category.append("LCOW")
            variable_list.append("Fixed Operating LCOW")
            unit_list.append("$/m3")            
        elif "LCOW_other_onm" in str(variable):
            value_list.append(value(m.fs.costing.LCOW_other_onm))
            up_name_list.append("System")
            category.append("LCOW")
            variable_list.append("Other O&M LCOW")
            unit_list.append("$/m3") 
        
        elif "operating_cost_annual" in str(variable):
            value_list.append(value(getattr(m.fs.costing, "operating_cost_annual")))
            up_name_list.append("System")
            category.append("Annual Cost")
            variable_list.append("System Total Operating Cost")
            unit_list.append("$MM/yr")   
        elif "fixed_op_cost_annual" in str(variable):
            value_list.append(value(getattr(m.fs.costing, "fixed_op_cost_annual")))
            up_name_list.append("System")
            category.append("Annual Cost")
            variable_list.append("System Fixed O&M")
            unit_list.append("$MM/yr")   
        elif "cat_and_chem_cost_annual" in str(variable):
            value_list.append(value(getattr(m.fs.costing, "cat_and_chem_cost_annual")))
            up_name_list.append("System")
            category.append("Annual Cost")
            variable_list.append("System Catalysts and Chemicals")
            unit_list.append("$MM/yr")   
        elif "electricity_cost_annual" in str(variable):
            value_list.append(value(getattr(m.fs.costing, "electricity_cost_annual")))
            up_name_list.append("System")
            category.append("Annual Cost")
            variable_list.append("System Electricity")
            unit_list.append("$MM/yr")  
        elif "other_var_cost_annual" in str(variable):
            value_list.append(value(getattr(m.fs.costing, "other_var_cost_annual")))
            up_name_list.append("System")
            category.append("Annual Cost")
            variable_list.append("Other Variable O&M")
            unit_list.append("$MM/yr")             
        
        elif "system_recovery" in str(variable):
            continue    
        else:
            variable_str = str(variable)[11:]
            up_name_list.append("System")
            variable_list.append("System " + name_lup.loc[variable_str].Excel_variable)
            value_list.append(value(getattr(m.fs.costing, variable_str)))
            unit_list.append(name_lup.loc[variable_str].Unit)
            category.append("Cost")
        
    value_list.append(value(m.fs.costing.electricity_intensity))
    up_name_list.append("System")
    category.append("Electricity")
    variable_list.append("Electricity Intensity")
    unit_list.append("kwh/m3")
    
    value_list.append(value(m.fs.costing.system_recovery)*100)
    up_name_list.append("System")
    category.append("Water Recovery")
    variable_list.append("Water Recovery")
    unit_list.append("%")    
        
    df = pd.DataFrame()
    df["Unit Process Name"] = up_name_list
    df["Variable"] = variable_list
    df["Value"] = value_list
    df["Metric"] = category
    df["Unit"] = unit_list
    df["Case Study"] = np.array(case_study)
    df["Scenario"] = np.array(scenario)  
    
    df["Metric"] = np.where(df.Unit == "$MM/yr", "Annual Cost", df.Metric)
    df["Metric"] = np.where(df.Unit == "$/m3", "LCOW", df.Metric)
                            
    # df.Value = df.Value.round(10)
    
    if save is True:
        df.to_csv("results/case_studies/%s_%s.csv" % (case_study, scenario), index=False)
    
    return df


def combine_case_study_results(case_study = None, save = True):

    final_df = pd.DataFrame()
    keyword = ('%s_' % case_study)
    for fname in os.listdir('./results/case_studies'):
        if keyword in fname:
            df = pd.read_csv('./results/case_studies/%s' % fname)

        final_df = pd.concat([final_df,df])

    if save is True:
        final_df.to_csv("%s_all_scenarios" % case_study)    
    
    return final_df

def compare_with_excel(excel_path, python_path):

    excel = pd.read_excel(excel_path)
    excel['Source'] = 'excel'

    py = pd.read_csv(python_path)
    py.rename(columns={"Unit Process Name": "Unit_Process", "Case Study": "Case_Study"}, inplace=True)
    py['Source'] = 'python'

    both = pd.concat([excel,py])
    pivot = pd.pivot_table(both, values='Value', 
                                index=['Case_Study','Scenario','Unit_Process','Variable','Unit'], 
                                columns=['Source']).reset_index()
    
    pivot.to_csv('results/check_with_excel.csv',index=False)

    return pivot

