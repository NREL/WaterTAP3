import numpy as np
import pandas as pd
import datetime
import time
import os, sys

from src import ml_regression

fixed_op_cost_scaling_exp = 0.7  # source:
basis_year = 2014  # meaning:
analysis_yr_cost_indicies = 2025
last_year_for_cost_indicies = 2050
on_stream_factor = 0.95

salaries_percent_FCI = 0.01  # represented as a fraction. source:
land_cost_precent_FCI = 0.0015  # represented as a fraction. source:
working_cap_precent_FCI = 0.05  # represented as a fraction. source:
maintinance_costs_precent_FCI = 0.03
lab_fees_precent_FCI = 0.01
insurance_taxes_precent_FCI = 0.007

benefit_percent_of_salary = 0.9

elec_price = 0.01


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
            df[ind_name] / df[df.Year == analysis_yr_cost_indicies][ind_name].max()
        )

    df = df.set_index(df.Year)

    return df


def total_up_cost(m=None, G=None, flow_in=0, cost_method="wt"):
    
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


def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()
