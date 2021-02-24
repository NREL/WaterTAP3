# Cleaning up input data csv's to be more python friendly

# Import python libraries
import numpy as np
import pandas as pd

# Open excel file, split the sheets into separate csv's
sheet1 = pd.read_excel('WT3Excel_Case_Study_Data_16Feb2021.xlsm', sheet_name='case_study_basis', index=True)
sheet1.to_csv("excel_case_study_basis.csv")

sheet2 = pd.read_excel('WT3Excel_Case_Study_Data_16Feb2021.xlsm', sheet_name='case_study_results', index=True)
sheet2.to_csv("excel_case_study_results.csv")

sheet3 = pd.read_excel('WT3Excel_Case_Study_Data_16Feb2021.xlsm', sheet_name='case_study_water_sources', index=True)
sheet3.to_csv("excel_case_study_water_sources.csv")

sheet4 = pd.read_excel('WT3Excel_Case_Study_Data_16Feb2021.xlsm', sheet_name='constituent_removal', index=True)
sheet4.to_csv("excel_constituent_removal.csv")

sheet5 = pd.read_excel('WT3Excel_Case_Study_Data_16Feb2021.xlsm', sheet_name='water_recovery', index=True)
sheet5.to_csv("excel_water_recovery.csv")



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
dataset['variable'].replace(to_replace="Base Employee Salary Cost per FCI", value="base_salary_per_FCI", inplace=True)

# Create new basis csv with friendlier python formatting
dataset.to_csv('case_study_basis.csv')



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

# Rename the words in the variable column to be lowercase
dataset['variable'] = dataset['variable'].str.lower()

# Create new results csv with friendlier python formatting
dataset.to_csv('case_study_results.csv')



############################################################################################################################################
############################################################################################################################################
####### CASE STUDY WATER SOURCES CSV
# Import data and delete the first column
dataset = pd.read_csv('excel_case_study_water_sources.csv', encoding='utf-8')
dataset = dataset.drop(dataset.columns[0], axis=1)

# Rename the columns to be lowercase
dataset.rename(columns={'Value': 'value', 'Reference': 'reference', 'WaterType': 'water_type', 'CaseStudy': 'case_study', 'Project': 'project', 'SourceOrUse': 'source_or_use'}, inplace=True)

# Duplicate "Variable" column and name it 'variable'
dataset['variable'] = dataset['Variable']

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


# Rename the words in the variable column to be lowercase
dataset['variable'] = dataset['variable'].str.lower()

# Create new results csv with friendlier python formatting
dataset.to_csv('case_study_water_sources.csv')





############################################################################################################################################
####### CONSTITUENT REMOVAL CSV
# Import data and delete the first column
dataset = pd.read_csv('excel_constituent_removal.csv', encoding='utf-8')
dataset = dataset.drop(dataset.columns[0], axis=1)

# Change "constituent" column to "constituent_longform"
dataset.rename(columns = {'constituent' : 'constituent_longform'}, inplace=True)

# Duplicate "constituent_longform" column and name it 'constituent'
dataset['constituent'] = dataset['constituent_longform']

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


a = range(7,16)
for x in a:
    dataset.drop('Unnamed: %s' % (x), axis=1, inplace=True)

# Replace parts of the constituent names to make them more python-friendly
dataset['constituent'] = dataset['constituent'].replace(to_replace=" ", value="_", regex=True)
dataset['constituent'] = dataset['constituent'].replace(to_replace=",", value="_", regex=True)
dataset['constituent'] = dataset['constituent'].replace(to_replace="-", value="_", regex=True)
dataset['constituent'] = dataset['constituent'].replace(to_replace='\(', value='', regex=True)
dataset['constituent'] = dataset['constituent'].replace(to_replace="\)", value="", regex=True)
dataset['constituent'] = dataset['constituent'].replace(to_replace="\.", value="", regex=True)


# Rename the words in the constituent column to be lowercase
dataset['constituent'] = dataset['constituent'].str.lower()

# Create new results csv with friendlier python formatting
dataset.to_csv('constituent_removal.csv')




############################################################################################################################################
############################################################################################################################################
####### WATER RECOVERY CSV
# Import data and delete the first column
dataset = pd.read_csv('excel_water_recovery.csv', encoding='utf-8')
dataset = dataset.drop(dataset.columns[0], axis=1)

# Rename the columns to be lowercase
dataset.rename(columns={'Case_Study': 'case_study', 'Scenario': 'scenario', 'Unit_Process': 'unit_process', 'Recovery': 'recovery', 'Evaporation': 'evaporation', 'Reference': 'reference'}, inplace=True)


# Simplify unit process names in new python-friendly unit process column
dataset['unit_process'].replace(to_replace="1-Hour_Holding_Tank", value="holding_tank", inplace=True)
dataset['unit_process'].replace(to_replace="3-Hour_Storage_Tank", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="6-Hour_Storage_Tank", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="12-Hour_Storage_Tank", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="24-Hour_Storage_Tank", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="48-Hour_Storage_Tank", value="treated_storage", inplace=True)
dataset['unit_process'].replace(to_replace="treated_storage_24_hr", value="treated_storage", inplace=True)

# Replace parts of the unit process names to make them more python-friendly
dataset['unit_process'] = dataset['unit_process'].replace(to_replace=" ", value="_", regex=True)
dataset['unit_process'] = dataset['unit_process'].replace(to_replace=",", value="_", regex=True)
dataset['unit_process'] = dataset['unit_process'].replace(to_replace="-", value="_", regex=True)
dataset['unit_process'] = dataset['unit_process'].replace(to_replace='\(', value='', regex=True)
dataset['unit_process'] = dataset['unit_process'].replace(to_replace="\)", value="", regex=True)
dataset['unit_process'] = dataset['unit_process'].replace(to_replace="\.", value="pt", regex=True)
dataset['unit_process'] = dataset['unit_process'].replace(to_replace="\/", value="_", regex=True)
dataset['unit_process'] = dataset['unit_process'].replace(to_replace="\+", value="plus", regex=True)



# Rename the words in the unit process column to be lowercase
dataset['unit_process'] = dataset['unit_process'].str.lower()

# Create new results csv with friendlier python formatting
dataset.to_csv('water_recovery.csv')