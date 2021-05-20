import numpy as np
import pandas as pd

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

    pivot.to_csv('check.csv',index=False)

    return pivot