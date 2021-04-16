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
def get_fixed_onm_reduction(m = None, reduction_value = 0.5):
    
    print("RUNNING 50% REDUCTION IN FIXED O&M SCENARIO")
    
    fixed_onm_variables = ["salaries_percent_FCI", "maintinance_costs_percent_FCI", "benefit_percent_of_salary", 
                "lab_fees_percent_FCI", "insurance_taxes_percent_FCI"]
        
    for fixed_onm_v in fixed_onm_variables:
        fix_value = value(getattr(m.fs.costing_param, fixed_onm_v)) * reduction_value
        getattr(m.fs.costing_param, fixed_onm_v).fix(fix_value)
        

    return m

