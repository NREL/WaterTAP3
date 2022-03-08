from pyomo.environ import value
from watertap3.utils import watertap_setup, get_case_study, run_watertap3, run_model, get_results_table
import pandas as pd
import numpy as np

__all__ = ['run_sensitivity', 'run_sensitivity_power', 'get_fixed_onm_reduction']

def run_sensitivity(m=None, save_results=False, return_results=False, scenario=None, case_study=None, tds_only=False):

    ro_list = ['reverse_osmosis', 'ro_first_pass', 'ro_a1', 'ro_b1',
               'ro_active', 'ro_restore', 'ro_first_stage']

    sens_df = pd.DataFrame()

    m_scenario = scenario
    case_print = m.fs.train['case_study'].replace('_', ' ').swapcase()
    scenario_print = m.fs.train['scenario'].replace('_', ' ').swapcase()

    m.fs.lcow_list = lcow_list = []
    m.fs.water_recovery_list = water_recovery_list = []
    m.fs.scenario_value = scenario_value = []
    m.fs.scenario_name = scenario_name = []
    m.fs.elec_lcow = elec_lcow = []
    m.fs.elec_int = elec_int = []
    m.fs.baseline_sens_value = baseline_sens_value = []
    m.fs.baseline_lcows = baseline_lcows = []
    m.fs.baseline_elect_ints = baseline_elect_ints = []
    m.fs.lcow_norm = lcow_norm = []
    m.fs.lcow_diff = lcow_diff = []
    m.fs.sens_vars = sens_vars = []
    m.fs.treated_water = treated_water = []
    m.fs.treated_water_norm = treated_water_norm = []
    m.fs.elect_int_norm = elect_int_norm = []
    m.fs.sens_var_norm = sens_var_norm = []
    m.fs.ro_pressure = ro_pressure = []
    m.fs.ro_press_norm = ro_press_norm = []
    m.fs.ro_area = ro_area = []
    m.fs.ro_area_norm = ro_area_norm = []
    m.fs.mem_replacement = mem_replacement = []

    baseline_treated_water = value(m.fs.costing.treated_water)
    baseline_lcow = value(m.fs.costing.LCOW)
    baseline_elect_int = value(m.fs.costing.electricity_intensity)

    lcow_list.append(value(m.fs.costing.LCOW))
    water_recovery_list.append(value(m.fs.costing.system_recovery))
    scenario_value.append('baseline')
    scenario_name.append(scenario)
    elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
    elec_int.append(value(m.fs.costing.electricity_intensity))
    baseline_sens_value.append(np.nan)
    baseline_lcows.append(baseline_lcow)
    baseline_elect_ints.append(baseline_elect_int)
    lcow_norm.append(1)
    lcow_diff.append(0)
    sens_vars.append('baseline')
    treated_water.append(value(m.fs.costing.treated_water))
    treated_water_norm.append(1)
    elect_int_norm.append(1)
    sens_var_norm.append(1)
    mem_replacement.append(None)
    ro_pressure.append(None)
    ro_press_norm.append(None)
    ro_area.append(None)
    ro_area_norm.append(None)

    runs_per_scenario = 20

    if tds_only:

        runs_per_scenario = 10

        lcow = []
        tci_total = []
        op_total = []
        op_annual = []
        fixed_op_annual = []
        other_annual = []
        elect_cost_annual = []
        elect_intens = []
        catchem_annual = []

        lcow.append(m.fs.costing.LCOW())
        tci_total.append(m.fs.costing.capital_investment_total())
        op_total.append(m.fs.costing.operating_cost_total())
        op_annual.append(m.fs.costing.operating_cost_annual())
        fixed_op_annual.append(m.fs.costing.fixed_op_cost_annual())
        other_annual.append(m.fs.costing.other_var_cost_annual())
        elect_cost_annual.append(m.fs.costing.electricity_cost_annual())
        elect_intens.append(m.fs.costing.electricity_intensity())
        catchem_annual.append(m.fs.costing.cat_and_chem_cost_annual())

        tds_in = False

        for key in m.fs.flow_in_dict:
            if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
                tds_in = True

        if tds_in:
            # print('\n-------', 'RESET', '-------\n')
            run_model_no_print(m=m, objective=False)
            # print('LCOW -->', m.fs.costing.LCOW())

            ############ Salinity +/- 30% ############
            stash_value = []
            tds_list = []
            for key in m.fs.flow_in_dict:
                if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
                    stash_value.append(value(getattr(m.fs, key).conc_mass_in[0, 'tds']))
            # print(stash_value)
            scenario = 'Inlet TDS +-25%'
            sens_var = 'tds_in'
            # print('-------', scenario, '-------')
            ub = 1.25
            lb = 0.75

            if case_study in ['cherokee', 'gila_river']:
                ub = 1.2
                lb = 0.8

            # if m_scenario in ['edr_ph_ro', 'ro_and_mf']:
            #     print('redoing upper and lower bounds')
            #     ub = 80
            #     lb = 60

            step = (ub - lb) / runs_per_scenario

            for i in np.arange(lb, ub + step, step):
                q = 0
                for key in m.fs.flow_in_dict:
                    if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
                        getattr(m.fs, key).conc_mass_in[0, 'tds'].fix(stash_value[q] * i)
                        q += 1
                # print('\n===============================')
                # print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
                # print('===============================\n')
                run_model_no_print(m=m, objective=False)

                scenario_value.append(sum(stash_value) * i)
                scenario_name.append(scenario)
                lcow.append(m.fs.costing.LCOW())
                tci_total.append(m.fs.costing.capital_investment_total())
                op_total.append(m.fs.costing.operating_cost_total())
                op_annual.append(m.fs.costing.operating_cost_annual())
                fixed_op_annual.append(m.fs.costing.fixed_op_cost_annual())
                other_annual.append(m.fs.costing.other_var_cost_annual())
                elect_cost_annual.append(m.fs.costing.electricity_cost_annual())
                elect_intens.append(m.fs.costing.electricity_intensity())
                catchem_annual.append(m.fs.costing.cat_and_chem_cost_annual())

            q = 0
            for key in m.fs.flow_in_dict:
                if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
                    getattr(m.fs, key).conc_mass_in[0, 'tds'].fix(stash_value[q])
                    q += 1

            run_model_no_print(m=m, objective=False)

            sens_df['scenario_name'] = scenario_name
            sens_df['scenario_value'] = scenario_value

            sens_df['lcow'] = lcow
            sens_df['tci_total'] = tci_total
            sens_df['op_total'] = op_total
            sens_df['op_annual'] = op_annual
            sens_df['fixed_op_annual'] = fixed_op_annual
            sens_df['other_annual'] = other_annual
            sens_df['elect_cost_annual'] = elect_cost_annual
            sens_df['elect_intens'] = elect_intens
            sens_df['catchem_annual'] = catchem_annual


            if save_results:
                sens_df.to_csv('results/case_studies/%s_%s_sensitivity.csv' % (case_study, m_scenario), index=False)
            if return_results:
                return sens_df
            else:
                return

            # print('\n====================== END SENSITIVITY ANALYSIS ======================\n')
    print('\n==================== STARTING SENSITIVITY ANALYSIS ===================\n')
    ############ Plant Capacity Utilization 70-100% ############
    stash_value = m.fs.costing_param.plant_cap_utilization()
    scenario = 'Plant Capacity Utilization 70-100%'
    sens_var = 'plant_cap'
    print('-------', scenario, '-------')
    ub = 1
    lb = 0.7
    step = (ub - lb) / runs_per_scenario
    for i in np.arange(lb, ub + step, step):

        m.fs.costing_param.plant_cap_utilization.fix(i)

        run_model(m=m, objective=False)

        print('\n===============================')
        print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
        print('===============================\n')
        print(scenario, i * 100, 'LCOW -->', m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i * 100)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))
        baseline_sens_value.append(stash_value)
        baseline_lcows.append(baseline_lcow)
        baseline_elect_ints.append(baseline_elect_int)
        lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
        lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
        sens_vars.append(sens_var)
        treated_water.append(value(m.fs.costing.treated_water))
        treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
        elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
        sens_var_norm.append(i / stash_value)
        ro_pressure.append(None)
        ro_press_norm.append(None)
        ro_area.append(None)
        ro_area_norm.append(None)
        mem_replacement.append(None)

    m.fs.costing_param.plant_cap_utilization.fix(stash_value)
    ############################################################

    print('\n-------', 'RESET', '-------\n')
    run_model(m=m, objective=False)
    print('LCOW -->', m.fs.costing.LCOW())

    ############ WACC 5-10%############
    stash_value = m.fs.costing_param.wacc()
    scenario = 'Weighted Average Cost of Capital 5-10%'
    sens_var = 'wacc'
    print('-------', scenario, '-------')
    ub = stash_value + 0.02
    lb = stash_value - 0.03
    step = (ub - lb) / runs_per_scenario
    for i in np.arange(lb, ub + step, step):
        print('\n===============================')
        print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
        print('===============================\n')
        m.fs.costing_param.wacc.fix(i)
        run_model(m=m, objective=False)
        print(scenario, i * 100, 'LCOW -->', m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i * 100)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))
        baseline_sens_value.append(stash_value)
        baseline_lcows.append(baseline_lcow)
        baseline_elect_ints.append(baseline_elect_int)
        lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
        lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
        sens_vars.append(sens_var)
        treated_water.append(value(m.fs.costing.treated_water))
        treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
        elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
        sens_var_norm.append(i / stash_value)
        ro_pressure.append(None)
        ro_press_norm.append(None)
        ro_area.append(None)
        ro_area_norm.append(None)
        mem_replacement.append(None)

    m.fs.costing_param.wacc.fix(stash_value)
    ############################################################

    tds_in = False

    for key in m.fs.flow_in_dict:
        if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
            tds_in = True

    if tds_in:
        print('\n-------', 'RESET', '-------\n')
        run_model(m=m, objective=False)
        print('LCOW -->', m.fs.costing.LCOW())

        ############ Salinity +/- 30% ############
        stash_value = []
        tds_list = []
        for key in m.fs.flow_in_dict:
            if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
                stash_value.append(value(getattr(m.fs, key).conc_mass_in[0, 'tds']))
        print(stash_value)
        scenario = 'Inlet TDS +-25%'
        sens_var = 'tds_in'
        print('-------', scenario, '-------')
        ub = 1.25
        lb = 0.75

        # if m_scenario in ['edr_ph_ro', 'ro_and_mf']:
        #     print('redoing upper and lower bounds')
        #     ub = 80
        #     lb = 60

        step = (ub - lb) / runs_per_scenario

        for i in np.arange(lb, ub + step, step):
            q = 0
            for key in m.fs.flow_in_dict:
                if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
                    getattr(m.fs, key).conc_mass_in[0, 'tds'].fix(stash_value[q] * i)
                    q += 1
            print('\n===============================')
            print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
            print('===============================\n')
            run_model(m=m, objective=False)
            print(scenario, sum(stash_value) * i, 'LCOW -->', m.fs.costing.LCOW())

            lcow_list.append(value(m.fs.costing.LCOW))
            water_recovery_list.append(value(m.fs.costing.system_recovery))
            scenario_value.append(sum(stash_value) * i)
            scenario_name.append(scenario)
            elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
            elec_int.append(value(m.fs.costing.electricity_intensity))
            baseline_sens_value.append(sum(stash_value))
            baseline_lcows.append(baseline_lcow)
            baseline_elect_ints.append(baseline_elect_int)
            lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
            lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
            sens_vars.append(sens_var)
            treated_water.append(value(m.fs.costing.treated_water))
            treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
            elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
            sens_var_norm.append(i)
            ro_pressure.append(None)
            ro_press_norm.append(None)
            ro_area.append(None)
            ro_area_norm.append(None)
            mem_replacement.append(None)

        q = 0
        for key in m.fs.flow_in_dict:
            if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
                getattr(m.fs, key).conc_mass_in[0, 'tds'].fix(stash_value[q])
                q += 1

    ############################################################
    if m_scenario not in ['edr_ph_ro', 'ro_and_mf']:
        if m.fs.train['case_study'] in ['cherokee', 'gila_river']:
            print('skips RO sens')
        else:
            print('\n-------', 'RESET', '-------\n')
            run_model(m=m, objective=False)
            print('LCOW -->', m.fs.costing.LCOW())
            ############ inlet flow +-25% ############
            m.fs.stash_value = stash_value = []
            for key in m.fs.flow_in_dict:
                stash_value.append(value(getattr(m.fs, key).flow_vol_in[0]))
            scenario = 'Inlet Flow +-25%'
            sens_var = 'flow_in'
            print('-------', scenario, '-------')
            ub = 1.25
            lb = 0.75
            step = (ub - lb) / runs_per_scenario

            for i in np.arange(lb, ub + step, step):
                # q = 0
                for q, key in enumerate(m.fs.flow_in_dict.keys()):
                    getattr(m.fs, key).flow_vol_in[0].fix(stash_value[q] * i)  # q += 1
                print('\n===============================')
                print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
                print('===============================\n')
                run_model(m=m, objective=False)
                print(scenario, stash_value[q] * i, 'LCOW -->', m.fs.costing.LCOW())

                lcow_list.append(value(m.fs.costing.LCOW))
                water_recovery_list.append(value(m.fs.costing.system_recovery))
                scenario_value.append(sum(stash_value) * i)
                scenario_name.append(scenario)
                elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
                elec_int.append(value(m.fs.costing.electricity_intensity))
                baseline_sens_value.append(sum(stash_value))
                baseline_lcows.append(baseline_lcow)
                baseline_elect_ints.append(baseline_elect_int)
                lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
                lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
                sens_vars.append(sens_var)
                treated_water.append(value(m.fs.costing.treated_water))
                treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
                elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
                sens_var_norm.append(i)
                ro_pressure.append(None)
                ro_press_norm.append(None)
                ro_area.append(None)
                ro_area_norm.append(None)
                mem_replacement.append(None)

            for q, key in enumerate(m.fs.flow_in_dict):
                getattr(m.fs, key).flow_vol_in[0].fix(stash_value[q])

    ############################################################
    print('\n-------', 'RESET', '-------\n')
    run_model(m=m, objective=False)
    print('LCOW -->', m.fs.costing.LCOW())
    ############ lifetime years ############

    stash_value = value(m.fs.costing_param.plant_lifetime_yrs)
    scenario = 'Plant Lifetime 15-45 yrs'
    sens_var = 'plant_life'
    print('-------', scenario, '-------')
    ub = 45
    lb = 15
    step = (ub - lb) / runs_per_scenario
    for i in np.arange(lb, ub + step, step):
        m.fs.costing_param.plant_lifetime_yrs = i
        print('\n===============================')
        print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
        print('===============================\n')
        run_model(m=m, objective=False)
        print(scenario, i, 'LCOW -->', m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))
        baseline_sens_value.append(stash_value)
        baseline_lcows.append(baseline_lcow)
        baseline_elect_ints.append(baseline_elect_int)
        lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
        lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
        sens_vars.append(sens_var)
        treated_water.append(value(m.fs.costing.treated_water))
        treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
        elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
        sens_var_norm.append(i - stash_value)
        ro_pressure.append(None)
        ro_press_norm.append(None)
        ro_area.append(None)
        ro_area_norm.append(None)
        mem_replacement.append(None)

    m.fs.costing_param.plant_lifetime_yrs = stash_value
    ############################################################
    print('\n-------', 'RESET', '-------\n')
    run_model(m=m, objective=False)
    print('LCOW -->', m.fs.costing.LCOW())
    ############ elec cost +-30% ############

    stash_value = value(m.fs.costing_param.electricity_price)
    scenario = 'Electricity Price +- 30%'
    sens_var = 'elect_price'
    print('-------', scenario, '-------')
    ub = stash_value * 1.3
    lb = stash_value * 0.7
    step = (ub - lb) / runs_per_scenario
    for i in np.arange(lb, ub + step, step):
        m.fs.costing_param.electricity_price = i
        print('\n===============================')
        print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
        print('===============================\n')
        run_model(m=m, objective=False)
        print(scenario, i * stash_value, 'LCOW -->', m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(i * stash_value)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))
        baseline_sens_value.append(stash_value)
        baseline_lcows.append(baseline_lcow)
        baseline_elect_ints.append(baseline_elect_int)
        lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
        lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
        sens_vars.append(sens_var)
        treated_water.append(value(m.fs.costing.treated_water))
        treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
        elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
        sens_var_norm.append(i / stash_value)
        ro_pressure.append(None)
        ro_press_norm.append(None)
        ro_area.append(None)
        ro_area_norm.append(None)
        mem_replacement.append(None)

    m.fs.costing_param.electricity_price = stash_value

    ############################################################
    print('\n-------', 'RESET', '-------\n')
    run_model(m=m, objective=False)
    print('LCOW -->', m.fs.costing.LCOW())

    # dwi_list = ['emwd', 'big_spring', 'kbhdp']
    # if m.fs.train['case_study'] in dwi_list:
    for key in m.fs.pfd_dict.keys():
        if m.fs.pfd_dict[key]['Unit'] == 'deep_well_injection':

            stash_value = value(getattr(m.fs, key).lift_height[0])
            scenario = 'Injection Pressure LH 100-2000 ft'
            sens_var = 'dwi_inj_pressure'
            print('-------', scenario, '-------')
            ub = 3500
            lb = 100
            step = (ub - lb) / runs_per_scenario
            for i in np.arange(lb, ub + step, step):
                getattr(m.fs, key).lift_height.fix(i)
                print('\n===============================')
                print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
                print('===============================\n')
                run_model(m=m, objective=False)
                print(scenario, i, 'LCOW -->', m.fs.costing.LCOW())

                lcow_list.append(value(m.fs.costing.LCOW))
                water_recovery_list.append(value(m.fs.costing.system_recovery))
                scenario_value.append(i)
                scenario_name.append(scenario)
                elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
                elec_int.append(value(m.fs.costing.electricity_intensity))
                baseline_sens_value.append(stash_value)
                baseline_lcows.append(baseline_lcow)
                baseline_elect_ints.append(baseline_elect_int)
                lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
                lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
                sens_vars.append(sens_var)
                treated_water.append(value(m.fs.costing.treated_water))
                treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
                elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
                sens_var_norm.append(i / stash_value)
                ro_pressure.append(None)
                ro_press_norm.append(None)
                ro_area.append(None)
                ro_area_norm.append(None)
                mem_replacement.append(None)

            getattr(m.fs, key).lift_height.fix(stash_value)

    ############################################################

    ############################################################
    print('\n-------', 'RESET', '-------\n')
    run_model(m=m, objective=False)
    print('LCOW -->', m.fs.costing.LCOW())
    ############ power sens -> adjust recovery of pre-evap pond to see evaporation area needs ############

    # cherokee
    # set RO recovery for ccro + brine to change, evap pond area unfixed and calculated by model, recovery set at 90%.
    # same for gila baseline

    m.fs.area_list = area_list = []

    # if m.fs.train['case_study'] == "cherokee" and m_scenario == "zld_ct":
    #     if 'reverse_osmosis_a' in m.fs.pfd_dict.keys():
    #         stash_value = value(getattr(m.fs, 'evaporation_pond').area[0])
    #         cenario = 'Area'
    #         sens_var = 'evap_pond_area'
    #         print('-------', scenario, '-------')
    #
    #         lb = 0.45
    #         ub = 0.95
    #         step = (ub - lb) / 50  # 50 runs
    #         getattr(m.fs, 'evaporation_pond').water_recovery.fix(0.9)
    #         getattr(m.fs, 'evaporation_pond').area.unfix()
    #
    #
    #         for recovery_rate in np.arange(lb, ub + step, step):
    #             m.fs.reverse_osmosis_a.kurby4 = Constraint(
    #                     expr=m.fs.reverse_osmosis_a.flow_vol_out[0] >=
    #                          (recovery_rate * m.fs.reverse_osmosis_a.flow_vol_in[0]))
    #             print('\n===============================')
    #             print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
    #             print('===============================\n')
    #             run_model(m=m, objective=False)
    #             print(scenario, recovery_rate, 'LCOW -->', m.fs.costing.LCOW())
    #
    #             lcow_list.append(value(m.fs.costing.LCOW))
    #             water_recovery_list.append(value(m.fs.costing.system_recovery))
    #             scenario_value.append(recovery_rate)
    #             scenario_name.append(scenario)
    #             elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
    #             elec_int.append(value(m.fs.costing.electricity_intensity))
    #             area_list.append(value(m.fs.evaporation_pond.area[0]))
    #
    #         getattr(m.fs, key).water_recovery.unfix()
    #         getattr(m.fs, key).area.fix(stash_value)
    #         df_area = pd.DataFrame(area_list)
    #         df_area.to_csv('results/case_studies/area_list_%s_%s_%s.csv' % (
    #                 m.fs.train['case_study'], m_scenario, key))

    #         for key in m.fs.pfd_dict.keys():
    #             if m.fs.pfd_dict[key]['Unit'] == 'evaporation_pond':

    #                 stash_value = value(getattr(m.fs, key).area[0])
    #                 scenario = 'Area'
    #                 sens_var = 'evap_pond_area'
    #                 print('-------', scenario, '-------')
    #                 if m.fs.train['case_study'] == 'cherokee':
    #                     ub = 1.5
    #                     lb = 0.75
    #                 if m.fs.train['case_study'] == 'gila_river':
    #                     lb = 0.5
    #                     ub = 1.05
    #                 step = (ub - lb) / 50  # 50 runs
    #                 for i in np.arange(lb, ub + step, step):
    #                     getattr(m.fs, key).area.fix(i * stash_value)
    #                     getattr(m.fs, key).water_recovery.unfix()
    #                     run_model(m=m, objective=False)
    #                     print(scenario, i * stash_value, 'LCOW -->', m.fs.costing.LCOW())

    #                     lcow_list.append(value(m.fs.costing.LCOW))
    #                     water_recovery_list.append(value(m.fs.costing.system_recovery))
    #                     scenario_value.append(i * stash_value)
    #                     scenario_name.append(scenario)
    #                     elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
    #                     elec_int.append(value(m.fs.costing.electricity_intensity))
    #                     area_list.append(value(m.fs.evaporation_pond.area[0]))

    #                 getattr(m.fs, key).area.fix(stash_value)
    #                 df_area = pd.DataFrame(area_list)
    #                 df_area.to_csv('results/case_studies/area_list_%s_%s_%s.csv' % (
    #                         m.fs.train['case_study'], m_scenario, key))

    ############################################################
    print('\n-------', 'RESET', '-------\n')
    run_model(m=m, objective=False)
    print('LCOW -->', m.fs.costing.LCOW())
    ############ RO scenarios --> pressure % change, membrane area, replacement rate% ############

    if m_scenario not in ['edr_ph_ro', 'ro_and_mf']:
        if m.fs.train['case_study'] in ['cherokee', 'gila_river', 'upw']:
            print('skips RO sens')
        else:
            for key in m.fs.pfd_dict.keys():
                if m.fs.pfd_dict[key]['Unit'] == 'reverse_osmosis':
                    if key in ro_list:
                        # if m.fs.train['case_study'] == 'ocwd':
                        #     m.fs.del_component(m.fs.ro_pressure_constr)
                        area = value(getattr(m.fs, key).membrane_area[0])
                        scenario_dict = {
                                'membrane_area': [-area * 0.2, area * 0.2],
                                'pressure': [0.85, 1.15],
                                'factor_membrane_replacement': [-0.1, 0.3]
                                }
                        for scenario in scenario_dict.keys():

                            print('\n-------', 'RESET', '-------\n')
                            run_model(m=m, objective=False)
                            print('LCOW -->', m.fs.costing.LCOW())

                            print('-------', scenario, '-------')
                            if scenario == 'pressure':
                                stash_value = value(getattr(getattr(getattr(m.fs, key), 'feed'), scenario)[0])
                                ub = stash_value * scenario_dict[scenario][1]
                                lb = stash_value * scenario_dict[scenario][0]
                            else:
                                stash_value = value(getattr(getattr(m.fs, key), scenario)[0])
                                ub = stash_value + scenario_dict[scenario][1]
                                lb = stash_value + scenario_dict[scenario][0]

                            step = (ub - lb) / runs_per_scenario

                            for i in np.arange(lb, ub + step, step):
                                if scenario == 'pressure':
                                    getattr(getattr(getattr(m.fs, key), 'feed'), scenario).fix(i)
                                else:
                                    getattr(getattr(m.fs, key), scenario).fix(i)
                                print('\n===============================')
                                print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
                                print('===============================\n')
                                run_model(m=m, objective=False)
                                print(scenario, i, 'LCOW -->', m.fs.costing.LCOW())

                                lcow_list.append(value(m.fs.costing.LCOW))
                                water_recovery_list.append(value(m.fs.costing.system_recovery))
                                scenario_value.append(i)
                                scenario_name.append(key + '_' + scenario)
                                elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
                                elec_int.append(value(m.fs.costing.electricity_intensity))
                                baseline_sens_value.append(stash_value)
                                baseline_lcows.append(baseline_lcow)
                                baseline_elect_ints.append(baseline_elect_int)
                                lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
                                lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
                                sens_vars.append(key + '_' + scenario)
                                treated_water.append(value(m.fs.costing.treated_water))
                                treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
                                elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
                                sens_var_norm.append(i / stash_value)
                                ro_pressure.append(value(getattr(getattr(getattr(m.fs, key), 'feed'), 'pressure')[0]))
                                ro_area.append(value(getattr(getattr(m.fs, key), 'membrane_area')[0]))
                                mem_replacement.append(value(getattr(getattr(m.fs, key), 'factor_membrane_replacement')[0]))
                                if scenario == 'pressure':
                                    ro_press_norm.append(ro_pressure[-1] / stash_value)
                                    ro_area_norm.append(None)
                                elif scenario == 'membrane_area':
                                    ro_area_norm.append(ro_area[-1] / stash_value)
                                    ro_press_norm.append(None)
                                elif scenario == 'factor_membrane_replacement':
                                    ro_area_norm.append(None)
                                    ro_press_norm.append(None)

                            if scenario == 'pressure':
                                getattr(getattr(getattr(m.fs, key), 'feed'), scenario).fix(stash_value)
                            else:
                                getattr(getattr(m.fs, key), scenario).fix(stash_value)

    ############################################################
    # in depth sens analysis #
    # if m.fs.train['case_study'] in ['san_luis']:
    #
    #     tds_in = False
    #
    #     for key in m.fs.flow_in_dict:
    #         if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
    #             tds_in = True
    #
    #     if tds_in is True:
    #         print('\n-------', 'RESET', '-------\n')
    #         run_model(m=m, objective=False)
    #         print('LCOW -->', m.fs.costing.LCOW())
    #
    #         ############ salinity  +-30% ############
    #         stash_value = []
    #         for key in m.fs.flow_in_dict:
    #             if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
    #                 stash_value.append(value(getattr(m.fs, key).conc_mass_in[0, 'tds']))
    #         print(stash_value)
    #         scenario = 'Inlet TDS +-25%'
    #         print('-------', scenario, '-------')
    #         ub = 1.25
    #         lb = 0.75
    #
    #         step = (ub - lb) / 1000
    #
    #         for i in np.arange(lb, ub + step, step):
    #             q = 0
    #             for key in m.fs.flow_in_dict:
    #                 if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
    #                     getattr(m.fs, key).conc_mass_in[0, 'tds'].fix(stash_value[q] * i)
    #                     q += 1
    #             print('\n===============================')
    #             print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
    #             print('===============================\n')
    #             run_model(m=m, objective=False)
    #             print(scenario, sum(stash_value) * i, 'LCOW -->', m.fs.costing.LCOW())
    #
    #             lcow_list.append(value(m.fs.costing.LCOW))
    #             water_recovery_list.append(value(m.fs.costing.system_recovery))
    #             scenario_value.append(sum(stash_value) * i)
    #             scenario_name.append(scenario)
    #             elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
    #             elec_int.append(value(m.fs.costing.electricity_intensity))
    #
    #         q = 0
    #         for key in m.fs.flow_in_dict:
    #             if 'tds' in list(getattr(m.fs, key).config.property_package.component_list):
    #                 getattr(m.fs, key).conc_mass_in[0, 'tds'].fix(stash_value[q])
    #                 q += 1

    ############################################################
    ############################################################
    ############################################################
    ############################################################

    # toc_in = False
    # for key in m.fs.flow_in_dict:
    #     if 'toc' in list(getattr(m.fs, key).config.property_package.component_list):
    #         toc_in = True
    #
    # if toc_in:
    #     print('\n-------', 'RESET', '-------\n')
    #     run_model(m=m, objective=False)
    #     print('LCOW -->', m.fs.costing.LCOW())
    #
    #     ############ TOC  +-30% ############
    #     stash_value = []
    #     for key in m.fs.flow_in_dict:
    #         if 'toc' in list(getattr(m.fs, key).config.property_package.component_list):
    #             stash_value.append(value(getattr(m.fs, key).conc_mass_in[0, 'toc']))
    #     print(stash_value)
    #     scenario = 'Inlet TOC +-25%'
    #     sens_var = 'toc_in'
    #     print('-------', scenario, '-------')
    #     ub = 1.25
    #     lb = 0.75
    #
    #     step = (ub - lb) / runs_per_scenario
    #
    #     for i in np.arange(lb, ub + step, step):
    #         q = 0
    #         for key in m.fs.flow_in_dict:
    #             if 'toc' in list(getattr(m.fs, key).config.property_package.component_list):
    #                 getattr(m.fs, key).conc_mass_in[0, 'toc'].fix(stash_value[q] * i)
    #                 q += 1
    #         print('\n===============================')
    #         print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
    #         print('===============================\n')
    #         run_model(m=m, objective=False)
    #         print(scenario, sum(stash_value) * i, 'LCOW -->', m.fs.costing.LCOW())
    #
    #         lcow_list.append(value(m.fs.costing.LCOW))
    #         water_recovery_list.append(value(m.fs.costing.system_recovery))
    #         scenario_value.append(sum(stash_value) * i)
    #         scenario_name.append(scenario)
    #         elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
    #         elec_int.append(value(m.fs.costing.electricity_intensity))
    #         baseline_sens_value.append(stash_value)
    #         baseline_lcows.append(baseline_lcow)
    #         baseline_elect_ints.append(baseline_elect_int)
    #         lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
    #         lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
    #         sens_vars.append(sens_var)
    #         treated_water.append(value(m.fs.costing.treated_water))
    #         treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
    #         elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
    #         sens_var_norm.append(i / stash_value)
    #
    #
    #     q = 0
    #     for key in m.fs.flow_in_dict:
    #         if 'toc' in list(getattr(m.fs, key).config.property_package.component_list):
    #             getattr(m.fs, key).conc_mass_in[0, 'toc'].fix(stash_value[q])
    #             q += 1

    print('\n-------', 'RESET', '-------\n')
    run_model(m=m, objective=False)
    print('LCOW -->', m.fs.costing.LCOW())

    ############ Component Replacement Costs -75% ############
    stash_value = m.fs.costing_param.maintenance_costs_percent_FCI()

    print(stash_value)
    scenario = 'Component Replacement Costs -75%'
    sens_var = 'component_replacement'
    print('-------', scenario, '-------')
    ub = 1
    lb = 0.1

    step = (ub - lb) / runs_per_scenario

    for i in np.arange(lb, ub + step, step):
        m.fs.costing_param.maintenance_costs_percent_FCI.fix(stash_value * i)
        print('\n===============================')
        print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}')
        print('===============================\n')
        run_model(m=m, objective=False)
        print(scenario, stash_value * i, 'LCOW -->', m.fs.costing.LCOW())

        lcow_list.append(value(m.fs.costing.LCOW))
        water_recovery_list.append(value(m.fs.costing.system_recovery))
        scenario_value.append(stash_value * i)
        scenario_name.append(scenario)
        elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
        elec_int.append(value(m.fs.costing.electricity_intensity))
        baseline_sens_value.append(stash_value)
        baseline_lcows.append(baseline_lcow)
        baseline_elect_ints.append(baseline_elect_int)
        lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
        lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
        sens_vars.append(sens_var)
        treated_water.append(value(m.fs.costing.treated_water))
        treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
        elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
        sens_var_norm.append((stash_value * i) / stash_value)
        ro_pressure.append(None)
        ro_press_norm.append(None)
        ro_area.append(None)
        ro_area_norm.append(None)
        mem_replacement.append(None)
    m.fs.costing_param.maintenance_costs_percent_FCI.fix(stash_value)
    ############################################################
    ############################################################
    ############################################################
    ############################################################

    if m.fs.train['case_study'] in ['monterey_one']:
        stash_value = m.fs.coag_and_floc.alum_dose[0]()
        print(stash_value)
        scenario = 'Alum Dose 0.5-20 mg/L'
        sens_var = 'alum_dose'
        print('-------', scenario, '-------')
        ub = 0.020
        lb = 0.0005
        step = (ub - lb) / runs_per_scenario
        for i in np.arange(lb, ub + step, step):
            m.fs.coag_and_floc.alum_dose.fix(i)
            print('\n===============================')
            print(f'CASE STUDY = {case_print}\nSCENARIO = {scenario_print}\n')
            print('===============================\n')
            run_model(m=m, objective=False)
            print(scenario, i, 'LCOW -->', m.fs.costing.LCOW())

            lcow_list.append(value(m.fs.costing.LCOW))
            water_recovery_list.append(value(m.fs.costing.system_recovery))
            scenario_value.append(i)
            scenario_name.append(scenario)
            elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
            elec_int.append(value(m.fs.costing.electricity_intensity))
            baseline_sens_value.append(value(stash_value))
            baseline_lcows.append(baseline_lcow)
            baseline_elect_ints.append(baseline_elect_int)
            lcow_norm.append(value(m.fs.costing.LCOW) / baseline_lcow)
            lcow_diff.append(value(m.fs.costing.LCOW) - baseline_lcow)
            sens_vars.append(sens_var)
            treated_water.append(value(m.fs.costing.treated_water))
            treated_water_norm.append(value(m.fs.costing.treated_water) / baseline_treated_water)
            elect_int_norm.append(value(m.fs.costing.electricity_intensity) / baseline_elect_int)
            sens_var_norm.append(value(i / stash_value))
            ro_pressure.append(None)
            ro_press_norm.append(None)
            ro_area.append(None)
            ro_area_norm.append(None)
            mem_replacement.append(None)

        m.fs.coag_and_floc.alum_dose.fix(stash_value)

    ############################################################

    # final run to get baseline numbers again
    run_model(m=m, objective=True)

    sens_df['sensitivity_var'] = sens_vars
    sens_df['baseline_sens_value'] = baseline_sens_value
    sens_df['scenario_value'] = scenario_value
    sens_df['sensitivity_var_norm'] = sens_var_norm
    sens_df['lcow'] = lcow_list
    sens_df['lcow_norm'] = lcow_norm
    sens_df['lcow_diff'] = lcow_diff
    sens_df['baseline_lcow'] = baseline_lcows
    sens_df['water_recovery'] = water_recovery_list
    sens_df['treated_water_vol'] = treated_water
    sens_df['baseline_treated_water'] = baseline_treated_water
    sens_df['treated_water_norm'] = treated_water_norm
    sens_df['elec_lcow'] = elec_lcow
    sens_df['baseline_elect_int'] = baseline_elect_ints
    sens_df['elec_int'] = elec_int
    sens_df['elect_int_norm'] = elect_int_norm
    sens_df['scenario_name'] = scenario_name
    sens_df['lcow_difference'] = sens_df.lcow - value(m.fs.costing.LCOW)
    sens_df['water_recovery_difference'] = (sens_df.water_recovery - value(m.fs.costing.system_recovery))
    sens_df['elec_lcow_difference'] = (sens_df.elec_lcow - value(m.fs.costing.elec_frac_LCOW))
    sens_df.elec_lcow = sens_df.elec_lcow * 100
    sens_df.water_recovery = sens_df.water_recovery * 100
    sens_df['ro_pressure'] = ro_pressure
    sens_df['ro_press_norm'] = ro_press_norm
    sens_df['ro_area'] = ro_area
    sens_df['ro_area_norm'] = ro_area_norm
    sens_df['mem_replacement'] = mem_replacement

    if save_results:
        sens_df.to_csv('results/case_studies/%s_%s_sensitivity.csv' % (case_study, m_scenario), index=False)
    if return_results:
        return sens_df

    print('\n====================== END SENSITIVITY ANALYSIS ======================\n')




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

def run_sensitivity_power(m=None, save_results=False, return_results=False, return_model=False, scenario=None,
                          case_study=None):
    ro_list = ['reverse_osmosis', 'ro_first_pass', 'ro_a1', 'ro_b1', 'ro_active', 'ro_restore']

    sens_df = pd.DataFrame()

    m_scenario = scenario

    m.fs.lcow_list = lcow_list = []
    m.fs.water_recovery_list = water_recovery_list = []
    m.fs.scenario_value = scenario_value = []
    m.fs.scenario_name = scenario_name = []
    m.fs.elec_lcow = elec_lcow = []
    m.fs.elec_int = elec_int = []
    m.fs.treated_water = treated_water = []
    m.fs.bc_elec = bc_elec = []
    m.fs.ro_elec = ro_elec = []

    m.fs.ro_a_pressure = ro_a_pressure = []
    m.fs.ro_a_elect_int = ro_a_elect_int = []
    m.fs.ro_a_elect_int_sys_treated = ro_a_elect_int_sys_treated = []
    m.fs.ro_a_elect_cost = ro_a_elect_cost = []
    m.fs.ro_a_recovery = ro_a_recovery = []
    m.fs.ro_a_capital = ro_a_capital = []
    m.fs.ro_a_om = ro_a_om = []
    m.fs.ro_a_flow_in = ro_a_flow_in = []
    m.fs.ro_a_flow_out = ro_a_flow_out = []
    m.fs.ro_a_area = ro_a_area = []
    m.fs.ro_a_tds_in = ro_a_tds_in = []
    m.fs.ro_a_tds_out = ro_a_tds_out = []
    m.fs.ro_a_flux = ro_a_flux = []
    m.fs.ro_a_mass_h2o = ro_a_mass_h2o = []
    m.fs.ro_a_f_osm = ro_a_f_osm = []
    m.fs.ro_a_r_osm = ro_a_r_osm = []
    m.fs.ro_a_mass_tds = ro_a_mass_tds = []
    m.fs.ro_a_salt_rej = ro_a_salt_rej = []
    m.fs.landfill_zld_tds = landfill_zld_tds = []


    m.fs.ro_area = ro_area = []
    m.fs.ro_pressure = ro_pressure = []
    m.fs.ro_elect_int = ro_elect_int = []
    m.fs.ro_elect_cost = ro_elect_cost = []
    m.fs.ro_recovery = ro_recovery = []
    m.fs.sys_elec = sys_elec = []
    m.fs.sys_elec_int = sys_elec_int = []
    m.fs.evap_flow_out = evap_flow_out = []
    m.fs.evap_flow_waste = evap_flow_waste = []
    m.fs.evap_capital = evap_capital = []
    m.fs.evap_recovery = evap_recovery = []
    m.fs.area_list = area_list = []

    if m.fs.train['case_study'] == "cherokee" and m_scenario == "zld_ct":
        if 'reverse_osmosis_a' in m.fs.pfd_dict.keys():
            stash_value = value(getattr(m.fs, 'evaporation_pond').area[0])
            scenario = 'Area'
            sens_var = 'evap_pond_area'
            print('-------', scenario, '-------')
            lb = 0.45
            ub = 0.99
            step = (ub - lb) / 50  # 50 runs
            m.fs.evaporation_pond.water_recovery.fix(0.892)
            m.fs.evaporation_pond.area.unfix()
            m.fs.reverse_osmosis_a.feed.pressure.unfix()
            m.fs.reverse_osmosis_a.membrane_area.unfix()

            recov_list = list(np.arange(lb, ub, step))
            recov_list.append(0.95)
            recov_list = sorted(recov_list)

            for recovery_rate in recov_list:
                # m.fs.reverse_osmosis_a.kurby4 = Constraint(expr=m.fs.reverse_osmosis_a.flow_vol_out[0] <= (recovery_rate * m.fs.reverse_osmosis_a.flow_vol_in[0]))
                m.fs.reverse_osmosis_a.kurby4 = Constraint(expr=m.fs.reverse_osmosis_a.flow_vol_out[0] / m.fs.reverse_osmosis_a.flow_vol_in[0] == recovery_rate)

                run_model(m=m, objective=True)
                print(scenario, recovery_rate, 'LCOW -->', m.fs.costing.LCOW())

                # print('evap pond recovery:', getattr(m.fs, 'evaporation_pond').water_recovery[0]())
                # print('evap pond area:', getattr(m.fs, 'evaporation_pond').area[0]())
                # print('RO recovery:', m.fs.reverse_osmosis_a.flow_vol_out[0]() / m.fs.reverse_osmosis_a.flow_vol_in[0]())

                lcow_list.append(value(m.fs.costing.LCOW))
                water_recovery_list.append(value(m.fs.costing.system_recovery))
                scenario_value.append(recovery_rate)
                scenario_name.append(scenario)
                elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
                elec_int.append(value(m.fs.costing.electricity_intensity))
                area_list.append(value(m.fs.evaporation_pond.area[0]))
                treated_water.append(m.fs.costing.treated_water())
                ro_a_elect_cost.append(m.fs.reverse_osmosis_a.costing.electricity_cost())
                ro_a_elect_int.append(m.fs.reverse_osmosis_a.electricity())
                ro_a_pressure.append(m.fs.reverse_osmosis_a.feed.pressure[0]())

                ro_a_recovery.append(m.fs.reverse_osmosis_a.ro_recovery())
                ro_a_capital.append(m.fs.reverse_osmosis_a.costing.total_cap_investment())
                ro_a_om.append(m.fs.reverse_osmosis_a.costing.annual_op_main_cost())
                ro_a_flow_in.append(m.fs.reverse_osmosis_a.flow_vol_in[0]())
                ro_a_flow_out.append(m.fs.reverse_osmosis_a.flow_vol_out[0]())
                ro_a_area.append(m.fs.reverse_osmosis_a.membrane_area[0]())
                ro_a_tds_in.append(m.fs.reverse_osmosis_a.conc_mass_in[0, 'tds']())
                ro_a_tds_out.append(m.fs.reverse_osmosis_a.conc_mass_out[0, 'tds']())
                ro_a_flux.append(m.fs.reverse_osmosis_a.flux_lmh())
                ro_a_mass_h2o.append(m.fs.reverse_osmosis_a.permeate.mass_flow_H2O[0]())
                ro_a_f_osm.append(m.fs.reverse_osmosis_a.feed.pressure_osm[0]())
                ro_a_r_osm.append(m.fs.reverse_osmosis_a.retentate.pressure_osm[0]())
                ro_a_mass_tds.append(m.fs.reverse_osmosis_a.permeate.mass_flow_tds[0]())
                ro_a_salt_rej.append(m.fs.reverse_osmosis_a.salt_rejection_conc())
                ro_a_elect_int_sys_treated.append(m.fs.reverse_osmosis_a.elec_int_treated())

                landfill_zld_tds.append(m.fs.landfill_zld.conc_mass_in[0, 'tds']())
                ro_elect_cost.append(m.fs.boiler_ro.costing.electricity_cost())
                ro_pressure.append(m.fs.boiler_ro.feed.pressure[0]())
                ro_elect_int.append(m.fs.boiler_ro.electricity())
                ro_recovery.append(m.fs.boiler_ro.ro_recovery())
                sys_elec.append(m.fs.costing.electricity_cost_annual())
                sys_elec_int.append(m.fs.costing.electricity_intensity())
                evap_flow_out.append(m.fs.evaporation_pond.flow_vol_out[0]())
                evap_flow_waste.append(m.fs.evaporation_pond.flow_vol_waste[0]())
                evap_capital.append(m.fs.evaporation_pond.costing.total_cap_investment())
                evap_recovery.append(m.fs.evaporation_pond.water_recovery[0]())

                # print('Electricity intensity', elec_int[-1])
                # print('Electricity intensity RO:', m.fs.reverse_osmosis_a.costing.elec_int_treated())
                # print('Electricity cost RO-A:', m.fs.reverse_osmosis_a.costing.electricity_cost())
                # print('Electricity intensity RO-B:', m.fs.boiler_ro.electricity())
                # print('Treated water:', m.fs.costing.treated_water())
                # print('Area', area_list)
                # print_ro_results(m)
            m.fs.evaporation_pond.water_recovery.unfix()
            m.fs.evaporation_pond.area.fix(stash_value)

    if m.fs.train['case_study'] == "gila_river" and m_scenario == "baseline":
        if 'reverse_osmosis' in m.fs.pfd_dict.keys():
            stash_value = value(getattr(m.fs, 'evaporation_pond').area[0])
            scenario = 'Area'
            sens_var = 'evap_pond_area'
            print('-------', scenario, '-------')

            lb = 0.45
            ub = 0.95
            step = (ub - lb) / 50  # 50 runs
            m.fs.evaporation_pond.water_recovery.fix(0.895)
            m.fs.evaporation_pond.area.unfix()

            m.fs.reverse_osmosis.feed.pressure.unfix()
            m.fs.reverse_osmosis.membrane_area.unfix()

            for recovery_rate in np.arange(lb, ub, step):
                # m.fs.reverse_osmosis.kurby4 = Constraint(expr=m.fs.reverse_osmosis.flow_vol_out[0] <= (recovery_rate * m.fs.reverse_osmosis.flow_vol_in[0]))
                # m.fs.reverse_osmosis.kurby5 = Constraint(expr=m.fs.reverse_osmosis.flow_vol_out[0] >= (recovery_rate * m.fs.reverse_osmosis.flow_vol_in[0]) * 0.99)
                m.fs.reverse_osmosis.kurby4 = Constraint(expr=m.fs.reverse_osmosis.flow_vol_out[0] / m.fs.reverse_osmosis.flow_vol_in[0] == recovery_rate)

                m.fs.brine_concentrator.water_recovery.fix(recovery_rate)

                run_model(m=m, objective=True)
                print(scenario, recovery_rate, 'LCOW -->', m.fs.costing.LCOW())

                print('evap pond recovery:', getattr(m.fs, 'evaporation_pond').water_recovery[0]())
                print('evap pond area:', getattr(m.fs, 'evaporation_pond').area[0]())
                print('RO recovery:', m.fs.reverse_osmosis.flow_vol_out[0]() / m.fs.reverse_osmosis.flow_vol_in[0]())
                lcow_list.append(value(m.fs.costing.LCOW))
                water_recovery_list.append(value(m.fs.costing.system_recovery))
                scenario_value.append(recovery_rate)
                scenario_name.append(scenario)
                elec_lcow.append(value(m.fs.costing.elec_frac_LCOW))
                elec_int.append(value(m.fs.costing.electricity_intensity))
                area_list.append(value(m.fs.evaporation_pond.area[0]))
                treated_water.append(m.fs.costing.treated_water())
                ro_a_elect_cost.append(m.fs.costing.electricity_cost_annual())
                bc_elec.append(m.fs.brine_concentrator.costing.electricity_cost())
                ro_elec.append(m.fs.reverse_osmosis.costing.electricity_cost())
                sys_elec.append(m.fs.costing.electricity_cost_annual())
                sys_elec_int.append(m.fs.costing.electricity_intensity())

                ro_elect_cost.append(m.fs.reverse_osmosis.costing.electricity_cost())
                ro_pressure.append(m.fs.reverse_osmosis.feed.pressure[0]())
                ro_elect_int.append(m.fs.reverse_osmosis.electricity())
                ro_recovery.append(m.fs.reverse_osmosis.ro_recovery())
                ro_area.append(m.fs.reverse_osmosis.membrane_area[0]())

            getattr(m.fs, 'evaporation_pond').water_recovery.unfix()
            getattr(m.fs, 'evaporation_pond').area.fix(stash_value)

    ############################################################
    # final run to get baseline numbers again
    print('\n-------', 'RESET', '-------\n')
    m = watertap_setup(case_study=case_study, scenario=m_scenario)
    m = get_case_study(m=m)
    bcr_df = pd.read_csv('data/baseline_cases_runs.csv')
    bcr_case_df = bcr_df[((bcr_df.case_study == case_study) & (bcr_df.scenario == m_scenario))].copy()
    desired_recovery = bcr_case_df.max_recovery_rate.iloc[0]
    ro_bounds = bcr_case_df.ro_bounds.iloc[0]
    m = run_watertap3(m, desired_recovery=desired_recovery, ro_bounds=ro_bounds)
    run_model(m=m, objective=False)
    print('LCOW without Objective -->', m.fs.costing.LCOW())

    run_model(m=m, objective=True)
    print('LCOW with Objective -->', m.fs.costing.LCOW())

    sens_df['lcow'] = lcow_list
    sens_df['lcow_difference'] = sens_df.lcow - value(m.fs.costing.LCOW)
    sens_df['lcow_norm'] = sens_df.lcow / value(m.fs.costing.LCOW)
    sens_df['system_recovery'] = water_recovery_list
    sens_df['elec_lcow'] = elec_lcow
    sens_df['elec_int'] = elec_int
    sens_df['target_ro_recovery'] = scenario_value
    # sens_df['scenario_name'] = scenario_name

    sens_df['sys_water_recovery_difference'] = (sens_df.system_recovery - value(m.fs.costing.system_recovery)) * 100
    sens_df['elec_lcow_difference'] = (sens_df.elec_lcow - value(m.fs.costing.elec_frac_LCOW))
    sens_df['evap_pond_area'] = area_list
    if case_study == 'cherokee':
        # sens_df['evap_pond_recovery'] = evap_recovery
        sens_df['ro_a_pressure'] = ro_a_pressure
        sens_df['ro_a_mem_area'] = ro_a_area
        sens_df['ro_a_recovery'] = ro_a_recovery
        sens_df['ro_a_elec_int'] = ro_a_elect_int
        sens_df['ro_a_elect_int_sys_treated'] = ro_a_elect_int_sys_treated

    if case_study == 'gila_river':
        sens_df['ro_pressure'] = ro_pressure
        sens_df['ro_mem_area'] = ro_area
        sens_df['ro_recovery'] = ro_recovery

    sens_df.elec_lcow = sens_df.elec_lcow * 100
    sens_df.system_recovery = sens_df.system_recovery * 100

    if save_results:
        sens_df.to_csv(f'results/case_studies/area_{case_study}_{m_scenario}_sensitivity.csv', index=False)

    if return_results and return_model:
        return m, sens_df
    elif return_results:
        return sens_df
    elif return_model:
        return m