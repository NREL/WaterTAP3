from pyomo.environ import value
from watertap3.utils import run_model, get_results_table

__all__ = ['get_fixed_onm_reduction']

# 50% fixed O&M reduction scenario
def get_fixed_onm_reduction(m = None, reduction_value_list = None, skip_small=None):
    
    print('RUNNING 50% REDUCTION IN FIXED O&M SCENARIO')
    
    fixed_onm_variables = ['salaries_percent_FCI', 'maintenance_costs_percent_FCI', 'benefit_percent_of_salary',
                'lab_fees_percent_FCI', 'insurance_taxes_percent_FCI']
    print(reduction_value_list)
    fixed_onm_v_dict = {}
    for fixed_onm_v in fixed_onm_variables:
        fixed_onm_v_dict[fixed_onm_v] = value(getattr(m.fs.costing_param, fixed_onm_v))

    for reduction_value in reduction_value_list:

        print("RUNNING REDUCTION FIXED O&M SCENARIO:", reduction_value)

        for fixed_onm_v in fixed_onm_variables:
            fix_value = fixed_onm_v_dict[fixed_onm_v] * reduction_value
            getattr(m.fs.costing_param, fixed_onm_v).fix(fix_value)

        run_model(m=m, objective=True, skip_small=skip_small, print_model_results="summary")
        df_no2 = get_results_table(m=m, case_study=m.fs.train["case_study"],
                                          scenario=("%s_fixed_onm_reduction" % (100 * reduction_value)))
        

    return m

