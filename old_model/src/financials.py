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


def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()
