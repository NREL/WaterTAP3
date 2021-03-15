# Cleaning up input data csv's to be more python friendly

# Import python libraries
import logging 
import sys

import numpy as np
import pandas as pd


# logging setup
fmt = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(format=fmt, level=logging.INFO)

# Open excel file, split the sheets into separate csv's
logging.info('beginning to read excel files')

excel_filename = 'WT3Excel_Case_Study_Data_12Mar2021.xlsm'

sheet1 = pd.read_excel(excel_filename, sheet_name='case_study_basis', index=True)
sheet1.to_csv("excel_case_study_basis.csv")

sheet2 = pd.read_excel(excel_filename, sheet_name='case_study_results', index=True)
sheet2.to_csv("excel_case_study_results.csv")

sheet3 = pd.read_excel(excel_filename, sheet_name='case_study_water_sources', index=True)
sheet3.to_csv("excel_case_study_water_sources.csv")

sheet4 = pd.read_excel(excel_filename, sheet_name='constituent_removal', index=True)
sheet4.to_csv("excel_constituent_removal.csv")

sheet5 = pd.read_excel(excel_filename, sheet_name='water_recovery', index=True)
sheet5.to_csv("excel_water_recovery.csv")

logging.info('finished reading excel files')


############################################################################################################################################
############################################################################################################################################
####### CASE STUDY BASIS CSV
# Import data
dataset = pd.read_csv('excel_case_study_basis.csv', encoding='utf-8')
dataset = dataset.drop(dataset.columns[0], axis=1)

# Rename the columns to be lowercase
dataset.rename(columns={'Case_Study': 'case_study', 'Scenario': 'scenario', 'Value': 'value', 'Reference': 'reference'}, inplace=True)

# Duplicate "Variable" column and name it 'variable'
dataset['variable'] = dataset['Variable']

# Add 'scenario' column
dataset = dataset.assign(reference='nawi')

# Delete 'Variable' column
dataset.drop('Variable',axis=1,inplace=True)

# Simplify variable names in new python-friendly variable column
dataset['variable'].replace(to_replace="Analysis Year (for Cost Indices)", value="analysis_year", inplace=True)
dataset['variable'].replace(to_replace="Basis for Plant Location", value="location_basis", inplace=True)
dataset['variable'].replace(to_replace="Plant Life (Yrs)", value="plant_life_yrs", inplace=True)
dataset['variable'].replace(to_replace="Land Cost as % of FCI", value="land_cost_percent", inplace=True)
dataset['variable'].replace(to_replace="Working Capital as % of FCI", value="working_capital_percent", inplace=True)
dataset['variable'].replace(to_replace="Salaries as % of FCI", value="salaries_percent", inplace=True)
dataset['variable'].replace(to_replace="Employee Benefits as % of Salaries", value="employee_benefits_percent", inplace=True)
dataset['variable'].replace(to_replace="Maintinance Costs as % of FCI", value="maintenance_cost_percent", inplace=True)
dataset['variable'].replace(to_replace="Laboratory Fees as % of FCI", value="laboratory_fees_percent", inplace=True)
dataset['variable'].replace(to_replace="Insurance and Taxes as % of FCI", value="insurance_and_taxes_percent", inplace=True)
dataset['variable'].replace(to_replace="Default Capital Scaling Exponent", value="default_cap_scaling_exp", inplace=True)
dataset['variable'].replace(to_replace="Default Fixed Opex Scaling Exponent", value="default_opex_scaling_exp", inplace=True)
dataset['variable'].replace(to_replace="Capital Financedy by Equity", value="cap_by_equity", inplace=True)
dataset['variable'].replace(to_replace="Debt Financing Interest Rate", value="debt_interest_rate", inplace=True)
dataset['variable'].replace(to_replace="Expected Return on Equity", value="exp_return_on_equity", inplace=True)
dataset['variable'].replace(to_replace="Default Capital Multipler (TPEC > FCI)", value="default_tpec_multiplier", inplace=True)
dataset['variable'].replace(to_replace="Default Capital Multipler (TIC > FCI)", value="default_tic_multiplier", inplace=True)
dataset['variable'].replace(to_replace="Base Employee Salary Cost per FCI", value="base_salary_per_fci", inplace=True)

# Chnage the name of vogtle_nuclear
dataset['case_study'].replace(to_replace="Vogtle_Nuclear", value="vogtle", inplace=True)
dataset['case_study'].replace(to_replace="Ultra_Pure_Water", value="upw", inplace=True)
dataset['case_study'].replace(to_replace="Monterey_One_Water", value="monterey_one", inplace=True)
dataset['case_study'].replace(to_replace="Iatan_Coal", value="iatan", inplace=True)

# Rename all the strings to be lowercase
dataset['case_study'] = dataset['case_study'].str.lower()
dataset['scenario'] = dataset['scenario'].str.lower()
dataset['reference'] = dataset['reference'].str.lower()
dataset['variable'] = dataset['variable'].str.lower()

# Make the location name lowercase in the 'value' column
dataset.loc[(dataset['variable'] == 'location_basis'), 'value'] = dataset['value'].str.lower()

# Replace parts of the case_study names to make them more python-friendly
dataset['case_study'] = dataset['case_study'].replace(to_replace="-", value="_", regex=True)

# Add rows for plant capacity utilization for each unit process
new_row = {'case_study': 'ashkelon', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'carlsbad', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'tampa_bay', 'scenario': 'baseline', 'value': '.75', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'santa_barbara', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'kbhdp', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'emwd', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'irwin', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'battery_park', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'big_spring', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'hrsd', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'ocwd', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'cherokee', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'uranium', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'san_luis', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'iron_and_steel', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'vogtle', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'damodar', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'kern_county', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'upw', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'pulp_and_paper', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'monterey_one', 'scenario': 'baseline', 'value': '.78', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'tuscarora', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'lithium', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'iatan', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'heap_leaching', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'beef_processing', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'case_study': 'produced_water_injection', 'scenario': 'baseline', 'value': '1', 'reference': 'nawi', 'variable': 'plant_cap_utilization'} 
dataset = dataset.append(new_row, ignore_index = True) 


# Create new basis csv with friendlier python formatting
dataset.to_csv('data/case_study_basis.csv')



############################################################################################################################################
############################################################################################################################################
####### CASE STUDY RESULTS CSV
# Import data and delete the first column
dataset = pd.read_csv('excel_case_study_results.csv', encoding='utf-8')
dataset = dataset.drop(dataset.columns[0], axis=1)

# Rename the columns to be lowercase
dataset.rename(columns={'Case_Study': 'case_study', 'Scenario': 'scenario', 'Train': 'train', 'Unit_Process': 'unit_process', 'Unit': 'unit', 'Value': 'value'}, inplace=True)

# Duplicate "Variable" column and name it 'variable'
dataset['variable'] = dataset['Variable']

# Rename "Variable" column to "variable_longform"
dataset.rename(columns={'Variable': 'variable_longform'}, inplace=True)

# Correct unit process names
dataset['unit_process'].replace(to_replace="treated_storage_24_hr", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="6-Hour_Storage_Tank", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="1-Hour_Storage_Tank", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="12-Hour_Storage_Tank", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="3-Hour_Storage_Tank", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="onsite_storage", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="Treated_Water_Storage", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="Chlorine_Addition_Cylinder", value="chlorination", inplace=True)
dataset['unit_process'].replace(to_replace="chlorination_twb", value="chlorination", inplace=True)
dataset['unit_process'].replace(to_replace="Chlorination  ", value="chlorination", inplace=True)
dataset['unit_process'].replace(to_replace="tri_media_filtration_with_backflush", value="tri_media_filtration", inplace=True)
dataset['unit_process'].replace(to_replace="Ferric_Chloride_FeCl3_Addition", value="ferric_chloride_addition", inplace=True)
dataset['unit_process'].replace(to_replace="UV_Irradiation_with_AOP ", value="uv_aop", inplace=True)
dataset['unit_process'].replace(to_replace="UV_Irradiation_with_AOP", value="uv_aop", inplace=True)
dataset['unit_process'].replace(to_replace="UV_Irradiation  ", value="uv_irradiation", inplace=True)
dataset['unit_process'].replace(to_replace="Brine RO", value="ro_deep", inplace=True)
dataset['unit_process'].replace(to_replace="Iron_Manganese_Removal", value="iron_and_manganese_removal", inplace=True)
dataset['unit_process'].replace(to_replace="media_fitration", value="media_filtration", inplace=True)
dataset['unit_process'].replace(to_replace="MBR_with_Nitrification", value="mbr_nitrification", inplace=True)
dataset['unit_process'].replace(to_replace="MBR_with_Denitrification", value="mbr_denitrification", inplace=True)
dataset['unit_process'].replace(to_replace="Ozonation_with_AOP", value="ozone_aop", inplace=True)
dataset['unit_process'].replace(to_replace="Pumping_Station", value="water_pumping_station", inplace=True)
dataset['unit_process'].replace(to_replace="Biological_Treatment_Fixed_Bed_Gravity_Basin", value="fixed_bed_gravity_basin", inplace=True)
dataset['unit_process'].replace(to_replace="Recharge_Basin_Pump_and_Well", value="recharge_pump_well", inplace=True)
dataset['unit_process'].replace(to_replace="Micro-Filtration  ", value="microfiltration", inplace=True)
dataset['unit_process'].replace(to_replace="micro_fitration", value="microfiltration", inplace=True)




# Simplify variable names in new python-friendly variable column
dataset['variable'].replace(to_replace="Fixed Capital Investment (FCI)", value="fixed_cap_inv", inplace=True)
dataset['variable'].replace(to_replace="Working Capital", value="working_cap", inplace=True)
dataset['variable'].replace(to_replace="Total Capital Investment (TCI)", value="total_cap_investment", inplace=True)
dataset['variable'].replace(to_replace="Catalysts and Chemicals", value="cat_and_chem_cost", inplace=True)
dataset['variable'].replace(to_replace="Electricity", value="electricity_cost", inplace=True)
dataset['variable'].replace(to_replace="Fuel and Other Utilities", value="none", inplace=True)
dataset['variable'].replace(to_replace="Replacement Parts", value="none", inplace=True)
dataset['variable'].replace(to_replace="Other Operating Costs", value="other_var_cost", inplace=True)
dataset['variable'].replace(to_replace="Total Variable Operating Costs", value="none", inplace=True)
dataset['variable'].replace(to_replace="Employee Salaries", value="salaries", inplace=True)
dataset['variable'].replace(to_replace="Laboratory", value="lab", inplace=True)
dataset['variable'].replace(to_replace="Insurance and Taxes", value="insurance_taxes", inplace=True)
dataset['variable'].replace(to_replace="Total Fixed Operating Costs", value="total_fixed_op_cost", inplace=True)
dataset['variable'].replace(to_replace="Capacity_Basis_for_Fixed_Capital_Cost", value="none", inplace=True)
dataset['variable'].replace(to_replace="Base_Fixed_Capital_Cost", value="none", inplace=True)
dataset['variable'].replace(to_replace="Capital_Scaling_Exponent", value="none", inplace=True)
dataset['variable'].replace(to_replace="Fixed_Op_Cost_Scaling_Exponent", value="fixed_op_cost_scaling_exp", inplace=True)
dataset['variable'].replace(to_replace="Basis_Year", value="base_year", inplace=True)
dataset['variable'].replace(to_replace="Capital_and_Replacement_Parts", value="cap_replacement_parts", inplace=True)
dataset['variable'].replace(to_replace="Catalysts_and_Chemicals", value="catalysts_chemicals", inplace=True)
dataset['variable'].replace(to_replace="Labor_and_Other_Fixed_Costs", value="labor_and_other_fixed", inplace=True)
dataset['variable'].replace(to_replace="Grid_Electricity", value="electricity", inplace=True)
dataset['variable'].replace(to_replace="Inlet Water", value="flow_vol_in", inplace=True)
dataset['variable'].replace(to_replace="Outlet Water", value="flow_vol_out", inplace=True)

# Rename the words to be lowercase
dataset['case_study'] = dataset['case_study'].str.lower()
dataset['scenario'] = dataset['scenario'].str.lower()
dataset['train'] = dataset['train'].str.lower()
dataset['variable'] = dataset['variable'].str.lower()
dataset['unit_process'] = dataset['unit_process'].str.lower()

# Replace parts of the unit_process names to make them more python-friendly
dataset['unit_process'] = dataset['unit_process'].replace(to_replace="-", value="_", regex=True)

# Drop any duplicate rows
dataset = dataset.drop_duplicates()

# Create new results csv with friendlier python formatting
dataset.to_csv('data/case_study_results.csv')



############################################################################################################################################
############################################################################################################################################
####### CASE STUDY WATER SOURCES CSV
# Import data and delete the first column
dataset = pd.read_csv('excel_case_study_water_sources.csv', encoding='utf-8')
dataset = dataset.drop(dataset.columns[0], axis=1)

# Rename the columns to be lowercase
dataset.rename(columns={'Value': 'value', 'Unit': 'unit', 'WaterType': 'water_type', 'CaseStudy': 'case_study', 'Project': 'reference', 'SourceOrUse': 'source_or_use'}, inplace=True)

# Add 'scenario' column
dataset = dataset.assign(scenario='baseline')

# Duplicate "Variable" column and name it 'variable'
dataset['variable'] = dataset['Variable']

# Delete 'Variable' and 'Reference' column
dataset.drop('Variable',axis=1,inplace=True)
dataset.drop('Reference',axis=1,inplace=True)

# Change the mg/L in the "unit" column to kg/m3
dataset['unit'].replace(to_replace="mg/L", value="kg/m3", inplace=True)

# Divide the values in the "value" column that are in kg/m3 by 1000
dataset.loc[(dataset['unit'] == 'kg/m3'), 'value'] = dataset['value'] / 1000

# Add a row for flow for each unit process
new_row = {'unit': 'm3/s', 'value': '4.5833', 'water_type': 'Seawater', 'case_study': 'Carlsbad', 'reference': 'NAWI', 'source_or_use': 'Source', 'scenario': 'baseline', 'variable': 'flow'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'unit': 'm3/s', 'value': '.3092', 'water_type': 'Seawater', 'case_study': 'Santa_Barbara', 'reference': 'NAWI', 'source_or_use': 'Source', 'scenario': 'baseline', 'variable': 'flow'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'unit': 'm3/s', 'value': '7.7819', 'water_type': 'Seawater', 'case_study': 'Ashkelon', 'reference': 'NAWI', 'source_or_use': 'Source', 'scenario': 'baseline', 'variable': 'flow'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'unit': 'm3/s', 'value': '1.92775', 'water_type': 'Seawater', 'case_study': 'Tampa_Bay', 'reference': 'NAWI', 'source_or_use': 'Source', 'scenario': 'baseline', 'variable': 'flow'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'unit': 'm3/s', 'value': '.285083333', 'water_type': 'Brackish', 'case_study': 'Irwin', 'reference': 'NAWI', 'source_or_use': 'Source', 'scenario': 'baseline', 'variable': 'flow'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'unit': 'm3/s', 'value': '1.336277778', 'water_type': 'KBHDP_Brackish_Low', 'case_study': 'KBHDP', 'reference': 'NAWI', 'source_or_use': 'Source', 'scenario': 'baseline', 'variable': 'flow'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'unit': 'm3/s', 'value': '1.336277778', 'water_type': 'KBHDP_Brackish_Ave', 'case_study': 'KBHDP', 'reference': 'NAWI', 'source_or_use': 'Source', 'scenario': 'baseline', 'variable': 'flow'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'unit': 'm3/s', 'value': '1.336277778', 'water_type': 'KBHDP_Brackish_High', 'case_study': 'KBHDP', 'reference': 'NAWI', 'source_or_use': 'Source', 'scenario': 'baseline', 'variable': 'flow'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'unit': 'm3/s', 'value': '.381', 'water_type': 'EMWD_CA_Brackish', 'case_study': 'EMWD', 'reference': 'NAWI', 'source_or_use': 'Source', 'scenario': 'baseline', 'variable': 'flow'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'unit': 'm3/s', 'value': '1.336277778', 'water_type': 'KBHDP_Brackish_Ave', 'case_study': 'KBHDP', 'reference': 'NAWI', 'source_or_use': 'Source', 'scenario': 'baseline', 'variable': 'flow'} 
dataset = dataset.append(new_row, ignore_index = True) 

# Simplify variable names in new python-friendly variable column
dataset['variable'].replace(to_replace="Boron, dissolved", value="boron", inplace=True)
dataset['variable'].replace(to_replace="Calcium, Dissolved", value="calcium", inplace=True)
dataset['variable'].replace(to_replace="Magnesium, Dissolved", value="magnesium", inplace=True)
dataset['variable'].replace(to_replace="Sodium, Dissolved", value="sodium", inplace=True)
dataset['variable'].replace(to_replace="Sulfate, Dissolved", value="sulfate", inplace=True)
dataset['variable'].replace(to_replace="Total Dissolved Solids (TDS)", value="tds", inplace=True)
dataset['variable'].replace(to_replace="Total Suspended Solids (TSS)", value="tss", inplace=True)
dataset['variable'].replace(to_replace="Nitrate (measured as Nitrogen)", value="nitrate_as_nitrogen", inplace=True)
dataset['variable'].replace(to_replace="Nitrite (measured as Nitrogen)", value="nitrite_as_nitrogen", inplace=True)
dataset['variable'].replace(to_replace="Silicon Dioxide (SiO2)", value="silicon_dioxide", inplace=True)
dataset['variable'].replace(to_replace="Total Organic Carbon (TOC)", value="toc", inplace=True)
dataset['variable'].replace(to_replace="Haloacetic acids (HAA5)", value="haloacetic_acids", inplace=True)
dataset['variable'].replace(to_replace="Nitrate-N, Dissolved", value="nitrate", inplace=True)
dataset['variable'].replace(to_replace="Total Trihalomethanes (TTHMs)", value="trihalomethanes", inplace=True)
dataset['variable'].replace(to_replace="Phosphates, Dissolved", value="phosphates", inplace=True)
dataset['variable'].replace(to_replace="Biological Oxygen Demand (BOD)", value="bod", inplace=True)
dataset['variable'].replace(to_replace="Chromium (total)", value="chromium", inplace=True)
dataset['variable'].replace(to_replace="Cyanide (as free cyanide)", value="cyanide_as_free", inplace=True)
dataset['variable'].replace(to_replace="Total Coliforms (including fecal coliform and E. Coli)", value="total_coliforms_fecal_ecoli", inplace=True)
dataset['variable'].replace(to_replace="1,2-Dibromo-3-chloropropane (DBCP)", value="dbcp", inplace=True)
dataset['variable'].replace(to_replace="2,4,5-TP (Silvex)", value="silvex", inplace=True)
dataset['variable'].replace(to_replace="Asbestos (fiber > 10 micrometers)", value="asbestos_fiber_10_micro_m", inplace=True)
dataset['variable'].replace(to_replace="Benzo(a)pyrene (PAHs)", value="PAHs", inplace=True)
dataset['variable'].replace(to_replace="Phosphorus - Total", value="phosphorus", inplace=True)
dataset['variable'].replace(to_replace="Di(2-ethylhexyl) adipate", value="di_2_ethylhexyl_adipate", inplace=True)
dataset['variable'].replace(to_replace="Di(2-ethylhexyl) phthalate", value="di_2_ethylhexyl_phthalate", inplace=True)
dataset['variable'].replace(to_replace="Estradiol Equivalency (EEQ)", value="eeq", inplace=True)
dataset['variable'].replace(to_replace="Heterotrophic plate count (HPC)", value="hpc", inplace=True)
dataset['variable'].replace(to_replace="Total Kjeldahl Nitrogen (TKN)", value="tkn", inplace=True)
dataset['variable'].replace(to_replace="N-nitrosodimethylamine (NDMA)", value="ndma", inplace=True)
dataset['variable'].replace(to_replace="Nitrogen - Total ", value="nitrogen", inplace=True)


# Change the water_type names
dataset['water_type'].replace(to_replace="Seawater_30", value="seawater", inplace=True)
dataset['water_type'].replace(to_replace="Seawater_31", value="seawater", inplace=True)
dataset['water_type'].replace(to_replace="Seawater_32", value="seawater", inplace=True)
dataset['water_type'].replace(to_replace="Seawater_33", value="seawater", inplace=True)
dataset['water_type'].replace(to_replace="Seawater_34", value="seawater", inplace=True)
dataset['water_type'].replace(to_replace="Seawater_35", value="seawater", inplace=True)
dataset['water_type'].replace(to_replace="Seawater_36", value="seawater", inplace=True)
dataset['water_type'].replace(to_replace="Seawater_37", value="seawater", inplace=True)
dataset['water_type'].replace(to_replace="Seawater_38", value="seawater", inplace=True)
dataset['water_type'].replace(to_replace="Seawater_39", value="seawater", inplace=True)
dataset['water_type'].replace(to_replace="Seawater_40", value="seawater", inplace=True)
dataset['water_type'].replace(to_replace="Seawater_41", value="seawater", inplace=True)
dataset['water_type'].replace(to_replace="Seawater_42", value="seawater", inplace=True)

dataset['water_type'].replace(to_replace="Irwin_Brackish", value="brackish", inplace=True)


# Change the case_study names
dataset['case_study'].replace(to_replace="Lithium_Mining", value="lithium", inplace=True)
dataset['case_study'].replace(to_replace="Uranium_Mining", value="uranium", inplace=True)


# Delete "Unnamed" columns
a = range(8,52)
for x in a:
    dataset.drop('Unnamed: %s' % (x), axis=1, inplace=True)

# Replace parts of the variable names to make them more python-friendly
dataset['variable'] = dataset['variable'].replace(to_replace=" ", value="_", regex=True)
dataset['variable'] = dataset['variable'].replace(to_replace=",", value="_", regex=True)
dataset['variable'] = dataset['variable'].replace(to_replace="-", value="_", regex=True)
dataset['variable'] = dataset['variable'].replace(to_replace='\(', value='', regex=True)
dataset['variable'] = dataset['variable'].replace(to_replace="\)", value="", regex=True)
dataset['variable'] = dataset['variable'].replace(to_replace="\.", value="", regex=True)

# Replace parts of the water_type names to make them more python-friendly
dataset['water_type'] = dataset['water_type'].replace(to_replace=" ", value="_", regex=True)
dataset['water_type'] = dataset['water_type'].replace(to_replace=",", value="_", regex=True)
dataset['water_type'] = dataset['water_type'].replace(to_replace="-", value="_", regex=True)
dataset['water_type'] = dataset['water_type'].replace(to_replace='\(', value='', regex=True)
dataset['water_type'] = dataset['water_type'].replace(to_replace="\)", value="", regex=True)
dataset['water_type'] = dataset['water_type'].replace(to_replace="\.", value="", regex=True)

# Replace parts of the case_study names to make them more python-friendly
dataset['case_study'] = dataset['case_study'].replace(to_replace="-", value="_", regex=True)


# Rename all the strings to be lowercase
dataset['water_type'] = dataset['water_type'].str.lower()
dataset['case_study'] = dataset['case_study'].str.lower()
dataset['reference'] = dataset['reference'].str.lower()
dataset['source_or_use'] = dataset['source_or_use'].str.lower()
dataset['variable'] = dataset['variable'].str.lower()
dataset['scenario'] = dataset['scenario'].str.lower()

# Drop any duplicate rows
dataset = dataset.drop_duplicates()

# Create new results csv with friendlier python formatting
dataset.to_csv('data/case_study_water_sources.csv')





############################################################################################################################################
####### CONSTITUENT REMOVAL CSV
# Import data and delete the first column
dataset = pd.read_csv('excel_constituent_removal.csv', encoding='utf-8')
dataset = dataset.drop(dataset.columns[0], axis=1)

# Change "constituent" column to "constituent_longform" and "reference" columns
dataset.rename(columns = {'constituent' : 'constituent_longform', 'reference' : 'ref'}, inplace=True)

# Duplicate "constituent_longform" column and name it 'constituent'
dataset['constituent'] = dataset['constituent_longform']

# Add two new columns
dataset = dataset.assign(scenario='Baseline')
dataset = dataset.assign(reference='NAWI')

# Add new rows to the dataframe
new_row = {'constituent_longform': 'Nitrate (measured as Nitrogen)', 'units': 'kg/m3', 'calculation_type': 'fractional_constituent_removal', 'unit_process': 'backwash_solids_handling', 'case_study': 'default', 'value': '.95', 'ref': 'default', 'constituent': 'nitrate', 'scenario': 'baseline', 'reference': 'nawi'} 
dataset = dataset.append(new_row, ignore_index = True) 
new_row = {'constituent_longform': 'Total Suspended Solids (TSS))', 'units': 'kg/m3', 'calculation_type': 'fractional_constituent_removal', 'unit_process': 'backwash_solids_handling', 'case_study': 'default', 'value': '.95', 'ref': 'default', 'constituent': 'tss', 'scenario': 'baseline', 'reference': 'nawi'} 
dataset = dataset.append(new_row, ignore_index = True)
new_row = {'constituent_longform': 'Total Organic Carbon (TOC)', 'units': 'kg/m3', 'calculation_type': 'fractional_constituent_removal', 'unit_process': 'backwash_solids_handling', 'case_study': 'default', 'value': '.95', 'ref': 'default', 'constituent': 'toc', 'scenario': 'baseline', 'reference': 'nawi'} 
dataset = dataset.append(new_row, ignore_index = True)

# Simplify constituent names in new python-friendly constituent column
dataset['constituent'].replace(to_replace="Boron, dissolved", value="boron", inplace=True)
dataset['constituent'].replace(to_replace="Calcium, Dissolved", value="calcium", inplace=True)
dataset['constituent'].replace(to_replace="Magnesium, Dissolved", value="magnesium", inplace=True)
dataset['constituent'].replace(to_replace="Sodium, Dissolved", value="sodium", inplace=True)
dataset['constituent'].replace(to_replace="Sulfate, Dissolved", value="sulfate", inplace=True)
dataset['constituent'].replace(to_replace="Total Dissolved Solids (TDS)", value="tds", inplace=True)
dataset['constituent'].replace(to_replace="Total Suspended Solids (TSS)", value="tss", inplace=True)
dataset['constituent'].replace(to_replace="Nitrate (measured as Nitrogen)", value="nitrate_as_nitrogen", inplace=True)
dataset['constituent'].replace(to_replace="Total Organic Carbon (TOC)", value="toc", inplace=True)
dataset['constituent'].replace(to_replace="Nitrate-N, Dissolved", value="nitrate", inplace=True)
dataset['constituent'].replace(to_replace="Phosphates, Dissolved", value="phosphates", inplace=True)
dataset['constituent'].replace(to_replace="Biological Oxygen Demand (BOD)", value="bod", inplace=True)
dataset['constituent'].replace(to_replace="Total Coliforms (including fecal coliform and E. Coli)", value="total_coliforms_fecal_ecoli", inplace=True)
dataset['constituent'].replace(to_replace="Estradiol Equivalency (EEQ)", value="eeq", inplace=True)
dataset['constituent'].replace(to_replace="N-nitrosodimethylamine (NDMA)", value="ndma", inplace=True)
dataset['constituent'].replace(to_replace="Chemical Oxygen Demand (COD)", value="cod", inplace=True)


# Correct unit process names
dataset['unit_process'].replace(to_replace="Microscreen_Filtration", value="micro_filtration", inplace=True)
dataset['unit_process'].replace(to_replace="tri_media_filtration_with_backflush", value="tri_media_filtration", inplace=True)
dataset['unit_process'].replace(to_replace="UV_Irradiation_with_AOP ", value="uv_aop", inplace=True)
dataset['unit_process'].replace(to_replace="UV_Irradiation  ", value="uv_irradiation", inplace=True)
dataset['unit_process'].replace(to_replace="MBR_with_Nitrification", value="mbr_nitrification", inplace=True)
dataset['unit_process'].replace(to_replace="MBR_with_Denitrification", value="mbr_denitrification", inplace=True)
dataset['unit_process'].replace(to_replace="Ozonation_with_AOP ", value="ozone_aop", inplace=True)
dataset['unit_process'].replace(to_replace="CAS_with_Denitrification ", value="cas_denitrif", inplace=True)
dataset['unit_process'].replace(to_replace="CAS_with_Nitrification ", value="cas_nitrif", inplace=True)
dataset['unit_process'].replace(to_replace="Micro-Filtration  ", value="microfiltration", inplace=True)


# Change the "mg/L" in the "units" column to "kg/m3"
dataset['units'].replace(to_replace="mg/L", value="kg/m3", inplace=True)


# Replace parts of the constituent names to make them more python-friendly
dataset['constituent'] = dataset['constituent'].replace(to_replace=" ", value="_", regex=True)
dataset['constituent'] = dataset['constituent'].replace(to_replace=",", value="_", regex=True)
dataset['constituent'] = dataset['constituent'].replace(to_replace="-", value="_", regex=True)
dataset['constituent'] = dataset['constituent'].replace(to_replace='\(', value='', regex=True)
dataset['constituent'] = dataset['constituent'].replace(to_replace="\)", value="", regex=True)
dataset['constituent'] = dataset['constituent'].replace(to_replace="\.", value="", regex=True)

dataset['unit_process'] = dataset['unit_process'].replace(to_replace="-", value="_", regex=True)

# Rename all the strings to be lowercase
dataset['case_study'] = dataset['case_study'].str.lower()
dataset['reference'] = dataset['reference'].str.lower()
dataset['scenario'] = dataset['scenario'].str.lower()
dataset['constituent'] = dataset['constituent'].str.lower()
dataset['unit_process'] = dataset['unit_process'].str.lower()

# Drop any duplicate rows
dataset = dataset.drop_duplicates()

# Create new results csv with friendlier python formatting
dataset.to_csv('data/constituent_removal.csv')




############################################################################################################################################
############################################################################################################################################
####### WATER RECOVERY CSV
# Import data and delete the first column
dataset = pd.read_csv('excel_water_recovery.csv', encoding='utf-8')
dataset = dataset.drop(dataset.columns[0], axis=1)

# Rename the columns to be lowercase
dataset.rename(columns={'Case_Study': 'case_study', 'Scenario': 'scenario', 'Unit_Process': 'unit_process', 'Recovery': 'recovery', 'Evaporation': 'evaporation', 'Reference': 'reference'}, inplace=True)

# Add a new row to the dataframe
new_row = {'case_study': 'Default', 'unit_process': 'ro_deep_scnd_pass', 'recovery': 'calculated', 'reference': 'Calculated value for total TDS removal from DEEP 5.1 model from IAEA'} 
dataset = dataset.append(new_row, ignore_index = True) 

# Simplify unit process names in new python-friendly unit process column
dataset['unit_process'].replace(to_replace="1-Hour_Holding_Tank", value="holding_tank", inplace=True)
dataset['unit_process'].replace(to_replace="3-Hour_Storage_Tank", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="6-Hour_Storage_Tank", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="12-Hour_Storage_Tank", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="24-Hour_Storage_Tank", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="48-Hour_Storage_Tank", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="treated_storage_24_hr", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="CAS_", value="cas", inplace=True)
dataset['unit_process'].replace(to_replace="CAS_+_Denitrif_", value="cas_denitrif", inplace=True)
dataset['unit_process'].replace(to_replace="CAS_+_Nitrif_", value="cas_nitrif", inplace=True)
dataset['unit_process'].replace(to_replace="Chlorination__", value="chlorination", inplace=True)
dataset['unit_process'].replace(to_replace="Deep_Well_", value="deep_well", inplace=True)
dataset['unit_process'].replace(to_replace="Microscreen_Filtration", value="micro_filtration", inplace=True)
dataset['unit_process'].replace(to_replace="tri_media_filtration_with_backflush", value="tri_media_filtration", inplace=True)
dataset['unit_process'].replace(to_replace="UV_Irradiation_with_AOP", value="uv_aop", inplace=True)
dataset['unit_process'].replace(to_replace="UV_Irradiation", value="uv_irradiation", inplace=True)
dataset['unit_process'].replace(to_replace="Pumping_Station", value="water_pumping_station", inplace=True)
dataset['unit_process'].replace(to_replace="MBR_and_Nitrification", value="mbr_nitrification", inplace=True)
dataset['unit_process'].replace(to_replace="MBR_and_Denitrification", value="mbr_denitrification", inplace=True)
dataset['unit_process'].replace(to_replace="Ozonation_with_AOP", value="ozone_aop", inplace=True)
dataset['unit_process'].replace(to_replace="Biological_Treatment_Fixed_Bed_Gravity_Basin", value="fixed_bed_gravity_basin", inplace=True)
dataset['unit_process'].replace(to_replace="Micro-Filtration", value="microfiltration", inplace=True)
dataset['unit_process'].replace(to_replace="Aeration_Multi-Stage_Bubble_Aeration", value="multi_stage_bubble_aeration", inplace=True)
dataset['unit_process'].replace(to_replace="Aeration_Packed_Tower_Aeration", value="packed_tower_aeration", inplace=True)
dataset['unit_process'].replace(to_replace="Biological_Treatment_Fluidized_Bed", value="fluidized_bed", inplace=True)
dataset['unit_process'].replace(to_replace="Biological_Treatment_Fixed_Bed_Pressure_Vessel", value="fixed_bed_pressure_vessel", inplace=True)
dataset['unit_process'].replace(to_replace="Agglomoration_and_Stacking_System", value="agglom_stacking", inplace=True)
dataset['unit_process'].replace(to_replace="Ore_Mining_to_Ore_Heap", value="heap_leaching", inplace=True)


# Replace parts of the unit process names to make them more python-friendly
dataset['unit_process'] = dataset['unit_process'].replace(to_replace=" ", value="_", regex=True)
dataset['unit_process'] = dataset['unit_process'].replace(to_replace=",", value="_", regex=True)
dataset['unit_process'] = dataset['unit_process'].replace(to_replace="-", value="_", regex=True)
dataset['unit_process'] = dataset['unit_process'].replace(to_replace='\(', value='', regex=True)
dataset['unit_process'] = dataset['unit_process'].replace(to_replace="\)", value="", regex=True)
dataset['unit_process'] = dataset['unit_process'].replace(to_replace="\.", value="pt", regex=True)
dataset['unit_process'] = dataset['unit_process'].replace(to_replace="\/", value="_", regex=True)
dataset['unit_process'] = dataset['unit_process'].replace(to_replace="\+", value="plus", regex=True)

# Change all recovery rates that are "1" to ".9999" so that Pyomo will work
dataset['recovery'].replace(to_replace="1", value=".9999", inplace=True)


# Rename all the strings to be lowercase
dataset['case_study'] = dataset['case_study'].str.lower()
dataset['scenario'] = dataset['scenario'].str.lower()
dataset['unit_process'] = dataset['unit_process'].str.lower()


# Remove coag_and_floc and tri_media_filtration
dataset = dataset[dataset.unit_process != 'coag_and_floc']
dataset = dataset[dataset.unit_process != 'tri_media_filtration']

# Add new coag_and_floc and tri_media_filtration rows with correct recovery rates
new_row = {'case_study': 'default', 'unit_process': 'coag_and_floc', 'recovery': '.9', 'reference': '(1) https://www.mrwa.com/WaterWorksMnl/Chapter%2012%20Coagulation.pdf, (2) Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura), (3) https://www.iwapublishing.com/news/coagulation-and-flocculation-water-and-wastewater-treatment, (4) Water and Wastewater Engineering: Design Principles and Practice (Mackenzie L. Davis).'} 
dataset = dataset.append(new_row, ignore_index = True)

new_row = {'case_study': 'default', 'unit_process': 'tri_media_filtration', 'recovery': '.9', 'reference': 'Texas Water Development Board IT3PR User Manual'} 
dataset = dataset.append(new_row, ignore_index = True) 

# Drop any duplicate rows
dataset = dataset.drop_duplicates()

# Create new results csv with friendlier python formatting
dataset.to_csv('data/water_recovery.csv')