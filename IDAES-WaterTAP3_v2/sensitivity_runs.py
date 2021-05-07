import pandas as pd
import ast

import numpy as np
import pandas as pd
from pyomo.network import Arc

import watertap as wt
from mixer_example import Mixer1
from split_test2 import Separator1
from pyomo.environ import value, Block

# 50% fixed O&M reduction scenario
def get_fixed_onm_reduction(m = None, reduction_value_list = None, skip_small=None):
        
    fixed_onm_variables = ["salaries_percent_FCI", "maintinance_costs_percent_FCI", "benefit_percent_of_salary", 
                "lab_fees_percent_FCI", "insurance_taxes_percent_FCI"]
    
    print(reduction_value_list)
    fixed_onm_v_dict = {}
    for fixed_onm_v in fixed_onm_variables:
        fixed_onm_v_dict[fixed_onm_v] = value(getattr(m.fs.costing_param, fixed_onm_v))
    
    for reduction_value in reduction_value_list:
        
        print("RUNNING REDUCTION FIXED O&M SCENARIO:", reduction_value)
        
        for fixed_onm_v in fixed_onm_variables:
            fix_value = fixed_onm_v_dict[fixed_onm_v] * reduction_value
            getattr(m.fs.costing_param, fixed_onm_v).fix(fix_value)
        
        wt.run_water_tap(m=m, objective=True, skip_small=skip_small, print_model_results="summary")
        df_no2 = wt.get_results_table(m=m, case_study=m.fs.train["case_study"], 
                                  scenario=("%s_fixed_onm_reduction" % (100*reduction_value)))
        
    return m

