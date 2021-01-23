from src import ml_regression
import pandas as pd
import numpy as np

def cost_curve_data2equation(filename="../WaterTAP3CostCurves.xlsx", sheet_name="CostData"): 

    df1 = pd.read_excel(filename, sheet_name=sheet_name)

    a_array = []; b_array = []; r2_result_array = []; y_unit = []; x_unit = [];

    for data_ids in df1.DataID.unique():
        pars, r2_result = ml_regression.get_cost_curve_coefs(data_id = data_ids)
        print(pars, r2_result)
        len(df1[df1.DataID == data_ids])
        a_array = a_array + ([pars[0]] * len(df1[df1.DataID == data_ids]))
        b_array = b_array + ([pars[1]] * len(df1[df1.DataID == data_ids]))
        r2_result_array = r2_result_array + ([r2_result] * len(df1[df1.DataID == data_ids]))
        y_unit = y_unit + ([df1[((df1.DataID == data_ids) & 
                                 (df1.VariableID == 1))].Unit.max()] * len(df1[df1.DataID == data_ids]))
        x_unit = x_unit + ([df1[((df1.DataID == data_ids) & 
                                 (df1.VariableID == 2))].Unit.max()] * len(df1[df1.DataID == data_ids]))

    df1['a'] = a_array
    df1['b'] = b_array
    df1['pearson_result'] = r2_result_array
    df1['y_unit'] = y_unit
    df1['x_unit'] = x_unit

    xx = df1.groupby("DataID").max()
    del xx["MultipleCurves"]
    del xx["VariableID"]
    del xx["VariableName"]
    del xx["Value"]
    del xx["Unit"]
    xx.to_csv("../WaterTAP3CostCurves_Out.csv")
    
    return xx


def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()   