import pandas as pd
from pylab import *
from pyomo.environ import Block, units as pyunits, value
from watertap3.utils import generate_constituent_list

__all__ = ['get_results_table', 'combine_case_study_results', 'compare_with_excel']

up_variables = ['fixed_cap_inv', 'fixed_cap_inv_unadjusted', 'land_cost', 'working_cap',
        'total_cap_investment', 'cat_and_chem_cost', 'electricity_cost', 'other_var_cost',
        'salaries', 'benefits', 'maintenance', 'lab', 'insurance_taxes', 'total_fixed_op_cost',
        'base_employee_salary_cost', 'electricity_cost', 'annual_op_main_cost']


def get_constituent_nice_name(con_str):
    con_dict = {
            'alkalinity_as_caco3': 'Alkalinity (as CaCO3)',
            'ammonia_nitrogen': 'NH4-N',
            'beta_particles_and_photon_emitters': 'Beta and Photon Emitters',
            'bicarbonate_alkalinity_as_caco3': 'Bicarbonate Alkalinity (as CaCO3)',
            'bod': 'BOD',
            'bod30': 'BOD30',
            'chemical_oxygen_demand_cod': 'COD',
            'cyanide_as_free': 'Free Cyanide',
            'nitrate_as_nitrogen': 'NO3-N',
            'nitrite_as_nitrogen': 'NO2-N',
            'ph_max': 'pH Max',
            'ph_min': 'pH Min',
            'phosphates': 'PO4',
            'radium_226': 'Radium-226',
            'radium_226_and_radium_228_combined': 'Radium-226 + Radium-228',
            'radium_228': 'Radium-228',
            'sulfate': 'SO4',
            'total_petroleum_hydrocarbons_tph': 'TPH',
            'trace_organic_chemicals_torc': 'TrOC',
            'total_coliforms_fecal_ecoli': 'Fecal Coliforms',
            'tds': 'TDS',
            'toc': 'TOC',
            'tss': 'TSS'
            }

    unit_dict = {
            'beta_particles_and_photon_emitters': 'pCi/L',
            'electrical_conductivity': 'S/m',
            'ph_max': 'pH',
            'ph_min': 'pH',
            'radium_226': 'pCi/L',
            'radium_226_and_radium_228_combined': 'pCi/L',
            'radium_228': 'pCi/L',
            'uranium': 'pCi/L',
            'turbidity': 'NTU'
            }
    if con_str in con_dict.keys():
        constituent = con_dict[con_str]
    else:
        constituent = con_str.replace('_', ' ').title()

    if con_str in unit_dict.keys():
        units = unit_dict[con_str]
    else:
        units = 'kg/m3'

    return constituent, units


def get_unit_nice_name(unit_str):
    up_dict = {
            'agglom_stacking': 'Agglom. Stacking',
            'anti_scalant_addition': 'Anit-Scalant Addition',
            'co2_addition': 'CO2 Addition',
            'gac': 'GAC',
            'gac_gravity': 'GAC - Gravity',
            'gac_gravity_2': 'GAC - Gravity 2',
            'gac_pressure_vessel': 'GAC - Pressure Vessel',
            'landfill_zld': 'Landfill ZLD',
            'ozone_aop': 'Ozone/AOP',
            'uv_aop': 'UV/AOP',
            'sw_onshore_intake': 'Seawater Intake',
            'abmet_intermediate_pump': 'ABMET Intermediate Pump',
            'abmet_intermediate_pump_2': 'ABMET Intermediate Pump 2',
            'abmet_interstage_pump': 'ABMET Interstage Pump',
            'abmet_interstage_pump_2': 'ABMET Interstage Pump 2',
            'bioreactor_bw_pump': 'Bioreactor BW Pump',
            'fab25': 'Fab25',
            'iron_and_manganese_removal': 'Fe/Mn Removal',
            'lp_transfer_pump': 'LP Transfer Pump',
            'lp_transfer_pump_2': 'LP Transfer Pump 2',
            'municipal_wwtp': 'Municipal WWTP',
            'uv_irradiation': 'UV Irradiation',
            'ph_adjustment': 'pH Adjustment',
            'ro_a_first_pass': 'RO-A First Pass',
            'ro_a_second_pass': 'RO-A Second Pass',
            'ro_a1': 'RO-A1',
            'ro_a2': 'RO-A2',
            'ro_b_first_pass': 'RO-B First Pass',
            'ro_b_second_pass': 'RO-B Second Pass',
            'ro_b1': 'RO-B1',
            'ro_b2': 'RO-B2',
            'ro_first_pass': 'RO First Pass',
            'ro_second_pass': 'RO Second Pass',
            'ro_first_stage': 'RO First Stage',
            'ro_second_stage': 'RO Second Stage',
            'ro_production': 'RO Production',
            'ro_active': 'RO Active',
            'ro_restore': 'RO Restore',
            'ro_restore_stage': 'RO Restore Stage',
            'ro_stage': 'RO Stage',
            'smp': 'SMP',
            'to_zld': 'To ZLD',
            'swift_pump': 'SWIFT Pump',
            'tri_media_filtration': 'Tri-Media Filtration',
            'ultra_filtration': 'Ultrafiltration',
            'ultra_filtration_2': 'Ultrafiltration 2',
            'uf_feed_pump': 'UF Feed Pump',
            'waiv': 'WAIV'
            }
    if unit_str in up_dict.keys():
        unit = up_dict[unit_str]
        return unit
    else:
        return unit_str.replace('_', ' ').title()


def get_results_table(m=None, scenario=None, case_study=None, save=True):
    if scenario is None:
        scenario = case_study_trains.train['scenario']
    if case_study is None:
        case_study = case_study_trains.train['case_study']

    pfd_dict = m.fs.pfd_dict
    m.fs.python_var = python_var = []
    m.fs.up_nice_name_list = up_nice_name_list = []
    m.fs.variable_list = variable_list = []
    m.fs.value_list = value_list = []
    m.fs.python_param = python_param = []
    category = []
    unit_list = []

    pressures = []
    recovs = []
    areas = []
    num_mems = []
    kws = []
    kss = []
    fluxs = []
    fluxs_lmh = []
    flow_ins_ro = []
    flow_outs_ro = []

    name_lup = pd.read_csv('data/excel_to_python_names.csv', index_col='Python_variable')

    for variable in m.fs.costing.component_objects():
        if 'CE_index' in str(variable):
            continue
        elif 'capital_recovery_factor' in str(variable):
            continue
        elif 'elec_frac_LCOW' in str(variable):
            value_list.append(value(m.fs.costing.elec_frac_LCOW))
            python_var.append('system')
            up_nice_name_list.append('System')
            python_param.append('elec_frac_LCOW')
            category.append('Electricity')
            variable_list.append('Electricity Fraction of LCOW')
            unit_list.append('$/m3')
        elif 'LCOW_TCI' in str(variable):
            value_list.append(value(m.fs.costing.LCOW_TCI))
            python_var.append('system')
            up_nice_name_list.append('System')
            python_param.append('LCOW_TCI')
            category.append('LCOW')
            variable_list.append('TCI LCOW')
            unit_list.append('$/m3')
        elif 'LCOW_elec' in str(variable):
            value_list.append(value(m.fs.costing.LCOW_elec))
            python_var.append('system')
            up_nice_name_list.append('System')
            python_param.append('LCOW_elec')
            category.append('LCOW')
            variable_list.append('Electricity LCOW')
            unit_list.append('$/m3')
        elif 'LCOW_fixed_op' in str(variable):
            value_list.append(value(m.fs.costing.LCOW_fixed_op))
            python_var.append('system')
            up_nice_name_list.append('System')
            python_param.append('LCOW_fixed_op')
            category.append('LCOW')
            variable_list.append('Fixed Operating LCOW')
            unit_list.append('$/m3')
        elif 'LCOW_chem' in str(variable):
            value_list.append(value(m.fs.costing.LCOW_chem))
            python_var.append('system')
            up_nice_name_list.append('System')
            python_param.append('LCOW_chem')
            category.append('LCOW')
            variable_list.append('Chemical LCOW')
            unit_list.append('$/m3')
        elif 'LCOW_other_onm' in str(variable):
            value_list.append(value(m.fs.costing.LCOW_other_onm))
            python_var.append('system')
            up_nice_name_list.append('System')
            python_param.append('LCOW_other_onm')
            category.append('LCOW')
            variable_list.append('Other O&M LCOW')
            unit_list.append('$/m3')
        elif 'operating_cost_annual' in str(variable):
            value_list.append(value(getattr(m.fs.costing, 'operating_cost_annual')))
            python_var.append('system')
            up_nice_name_list.append('System')
            python_param.append('operating_cost_annual')
            category.append('Annual Cost')
            variable_list.append('System Total Operating Cost')
            unit_list.append('$MM/yr')
        elif 'fixed_op_cost_annual' in str(variable):
            value_list.append(value(getattr(m.fs.costing, 'fixed_op_cost_annual')))
            python_var.append('system')
            up_nice_name_list.append('System')
            python_param.append('fixed_op_cost_annual')
            category.append('Annual Cost')
            variable_list.append('System Fixed O&M')
            unit_list.append('$MM/yr')
        elif 'cat_and_chem_cost_annual' in str(variable):
            value_list.append(value(getattr(m.fs.costing, 'cat_and_chem_cost_annual')))
            python_var.append('system')
            up_nice_name_list.append('System')
            python_param.append('cat_and_chem_cost_annual')
            category.append('Annual Cost')
            variable_list.append('System Catalysts and Chemicals')
            unit_list.append('$MM/yr')
        elif 'electricity_cost_annual' in str(variable):
            value_list.append(value(getattr(m.fs.costing, 'electricity_cost_annual')))
            python_var.append('system')
            up_nice_name_list.append('System')
            python_param.append('electricity_cost_annual')
            category.append('Annual Cost')
            variable_list.append('System Electricity')
            unit_list.append('$MM/yr')
        elif 'other_var_cost_annual' in str(variable):
            value_list.append(value(getattr(m.fs.costing, 'other_var_cost_annual')))
            python_var.append('system')
            up_nice_name_list.append('System')
            python_param.append('other_var_cost_annual')
            category.append('Annual Cost')
            variable_list.append('Other Variable O&M')
            unit_list.append('$MM/yr')

        elif 'system_recovery' in str(variable):
            continue
        elif 'electricity_intensity' in str(variable):
            continue
        else:
            variable_str = str(variable)[11:]
            python_var.append('system')
            up_nice_name_list.append('System')
            python_param.append(variable_str)
            variable_list.append('System ' + name_lup.loc[variable_str].Excel_variable)
            value_list.append(value(getattr(m.fs.costing, variable_str)))
            unit_list.append(name_lup.loc[variable_str].Unit)
            category.append('Cost')

    intake_str = [k for k, v in m.fs.pfd_dict.items() if v['Type'] == 'intake']
    waste_str = [k for k, v in m.fs.pfd_dict.items() if v['Type'] == 'waste']

    intakes = [b_unit for b_unit in m.fs.component_objects(Block, descend_into=False) if
               hasattr(b_unit, 'flow_vol_in') and str(b_unit)[3:] in intake_str]
    wastes = [b_unit for b_unit in m.fs.component_objects(Block, descend_into=False) if
              hasattr(b_unit, 'flow_vol_in') and str(b_unit)[3:] in waste_str]

    flow_ins = [getattr(intake, 'flow_vol_in')[0]() for intake in intakes]
    flow_wastes = [getattr(waste, 'flow_vol_in')[0]() for waste in wastes]

    sys_flow_in = sum(flow_ins)
    sys_flow_waste = sum(flow_wastes)

    value_list.append(value(m.fs.costing.electricity_intensity))
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('electricity_intensity')
    category.append('Electricity')
    variable_list.append('Electricity Intensity System Treated')
    unit_list.append('kWh/m3')

    value_list.append(value(m.fs.costing.electricity_intensity))
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('electricity_intensity')
    category.append('Electricity')
    variable_list.append('Electricity Intensity')
    unit_list.append('kWh/m3')

    value_list.append(value(m.fs.costing.system_recovery) * 100)
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('system_recovery')
    category.append('Water Flow')
    variable_list.append('Water Recovery')
    unit_list.append('%')

    value_list.append(value(m.fs.costing.treated_water))
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('treated_water')
    category.append('Water Flow')
    variable_list.append('System Treated Flow')
    unit_list.append('m3/s')

    value_list.append(sys_flow_in)
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('sys_flow_in')
    category.append('Water Flow')
    variable_list.append('System Inlet Flow')
    unit_list.append('m3/s')

    value_list.append(sys_flow_waste)
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('sys_flow_waste')
    category.append('Water Flow')
    variable_list.append('System Waste Flow')
    unit_list.append('m3/s')

    value_list.append(m.fs.costing.capital_recovery_factor)
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('capital_recovery_factor')
    category.append('Costing')
    variable_list.append('Capital Recovery Factor')
    unit_list.append('%')

    value_list.append(m.fs.costing_param.wacc)
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('wacc')
    category.append('Costing')
    variable_list.append('WACC')
    unit_list.append('%')

    value_list.append(m.fs.costing_param.plant_cap_utilization)
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('plant_cap_utilization')
    category.append('Costing')
    variable_list.append('Plant Capacity Utilization')
    unit_list.append('%')

    value_list.append(m.fs.costing_param.plant_lifetime_yrs)
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('plant_lifetime_yrs')
    category.append('Costing')
    variable_list.append('Plant Lifetime')
    unit_list.append('Years')

    value_list.append(value(m.fs.costing_param.electricity_price))
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('electricity_price')
    category.append('Costing')
    variable_list.append('Electricity Price')
    unit_list.append('$/kWh')

    value_list.append(0)
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('location')
    category.append('Costing')
    variable_list.append('Location')
    unit_list.append(m.fs.costing_param.location.title())

    value_list.append(m.fs.costing_param.analysis_yr_cost_indicies)
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('analysis_yr_cost_indicies')
    category.append('Costing')
    variable_list.append('Analysis Year Basis')
    unit_list.append(None)

    value_list.append(value(m.fs.costing_param.maintenance_costs_percent_FCI))
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('maintenance_costs_percent_FCI')
    category.append('Costing')
    variable_list.append('Maintenance Costs % FCI')
    unit_list.append('%')

    value_list.append(value(m.fs.costing_param.salaries_percent_FCI))
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('salaries_percent_FCI')
    category.append('Costing')
    variable_list.append('Salaries % FCI')
    unit_list.append('%')

    value_list.append(value(m.fs.costing_param.benefit_percent_of_salary))
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('benefit_percent_of_salary')
    category.append('Costing')
    variable_list.append('Benefits % FCI')
    unit_list.append('%')

    value_list.append(value(m.fs.costing_param.insurance_taxes_percent_FCI))
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('insurance_taxes_percent_FCI')
    category.append('Costing')
    variable_list.append('Insurance/Taxes % FCI')
    unit_list.append('%')

    value_list.append(value(m.fs.costing_param.lab_fees_percent_FCI))
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('lab_fees_percent_FCI')
    category.append('Costing')
    variable_list.append('Lab % FCI')
    unit_list.append('%')

    value_list.append(value(m.fs.costing_param.land_cost_percent_FCI))
    python_var.append('system')
    up_nice_name_list.append('System')
    python_param.append('land_cost_percent_FCI')
    category.append('Costing')
    variable_list.append('Land Cost % FCI')
    unit_list.append('%')

    for b_unit in m.fs.component_objects(Block, descend_into=False):
        unit = b_unit
        unit_str = unit_name = str(b_unit)[3:]
        up_nice_name = get_unit_nice_name(unit_str)

        if hasattr(b_unit, 'electricity'):
            python_var.append(unit_str)
            up_nice_name_list.append(up_nice_name)
            python_param.append('electricity')
            variable_list.append('Electricity Intensity Unit Inlet')
            value_list.append(value(getattr(b_unit, 'electricity')))
            unit_list.append('kWh/m3')
            category.append('Electricity')

        if hasattr(b_unit, 'elec_int_treated'):
            python_var.append(unit_str)
            up_nice_name_list.append(up_nice_name)
            python_param.append('elec_int_treated')
            variable_list.append('Electricity Intensity System Treated')
            value_list.append(value(b_unit.elec_int_treated))
            unit_list.append('kWh/m3')
            category.append('Electricity')

        if hasattr(b_unit, 'costing'):
            if hasattr(b_unit, 'LCOW'):
                python_var.append(unit_str)
                up_nice_name_list.append(up_nice_name)
                python_param.append('LCOW')
                category.append('LCOW')
                variable_list.append('Unit Levelized Cost')
                value_list.append(value(b_unit.LCOW))
                unit_list.append('$/m3')

            for variable in up_variables:
                python_var.append(unit_str)
                up_nice_name_list.append(up_nice_name)
                if variable == 'annual_op_main_cost':
                    variable_list.append('Annual O&M Costs')
                    value_list.append(value(getattr(b_unit.costing, variable)))
                    unit_list.append('$MM/yr')
                    python_param.append(variable)
                elif variable == 'fixed_cap_inv_unadjusted':
                    variable_list.append('Fixed Capital Investment (unadj)')
                    value_list.append(value(getattr(b_unit.costing, variable)))
                    unit_list.append('$MM')
                    python_param.append(variable)
                else:
                    variable_list.append(name_lup.loc[variable].Excel_variable)
                    value_list.append(value(getattr(b_unit.costing, variable)))
                    unit_list.append(name_lup.loc[variable].Unit)
                    python_param.append(variable)
                if variable == 'electricity':
                    category.append('Electricity')
                else:
                    category.append('Cost')

            value_list.append((value(getattr(m.fs, unit_str).flow_vol_in[0])))
            python_var.append(unit_str)
            up_nice_name_list.append(up_nice_name)
            variable_list.append('Inlet Water Flow')
            category.append('Water Flow')
            unit_list.append('m3/s')
            python_param.append('flow_vol_in')

            value_list.append((value(getattr(m.fs, unit_str).flow_vol_out[0])))
            python_var.append(unit_str)
            up_nice_name_list.append(up_nice_name)
            variable_list.append('Outlet Water Flow')
            category.append('Water Flow')
            unit_list.append('m3/s')
            python_param.append('flow_vol_out')

            value_list.append(value(getattr(m.fs, unit_str).flow_vol_waste[0]))
            python_var.append(unit_str)
            up_nice_name_list.append(up_nice_name)
            variable_list.append('Waste Water Flow')
            category.append('Water Flow')
            unit_list.append('m3/s')
            python_param.append('flow_vol_waste')

            value_list.append(value(getattr(m.fs, unit_str).flow_vol_out[0]) /
                              value(getattr(m.fs, unit_str).flow_vol_in[0]))
            python_var.append(unit_str)
            up_nice_name_list.append(up_nice_name)
            variable_list.append('Unit Water Recovery')
            category.append('Water Flow')
            unit_list.append('%')
            python_param.append('water_recovery')

            if unit_name in pfd_dict.keys() and pfd_dict[unit_name]['Unit'] == 'reverse_osmosis':

                pressures.append(unit.feed.pressure[0]())
                recovs.append(unit.ro_recovery())
                areas.append(unit.membrane_area[0]())
                num_mems.append(unit.num_membranes())
                kws.append(unit.a[0]())
                kss.append(unit.b[0]())
                fluxs.append(unit.flux())
                fluxs_lmh.append(unit.flux_lmh())
                flow_ins_ro.append(unit.flow_vol_in[0]())
                flow_outs_ro.append(unit.flow_vol_out[0]())
                # recovs.append(unit.flow_vol_out[0]() / unit.flow_vol_in[0]())

                value_list.append(pressures[-1])
                python_var.append(unit_str)
                up_nice_name_list.append(up_nice_name)
                category.append('Reverse Osmosis')
                variable_list.append('Pressure')
                python_param.append('feed.pressure')
                unit_list.append('bar')

                value_list.append(recovs[-1])
                python_var.append(unit_str)
                up_nice_name_list.append(up_nice_name)
                category.append('Reverse Osmosis')
                variable_list.append('RO Recovery')
                python_param.append('ro_recovery')
                unit_list.append('%')

                value_list.append(areas[-1])
                python_var.append(unit_str)
                up_nice_name_list.append(up_nice_name)
                category.append('Reverse Osmosis')
                variable_list.append('Membrane Area')
                python_param.append('membrane_area')
                unit_list.append('m2')

                value_list.append(num_mems[-1])
                python_var.append(unit_str)
                up_nice_name_list.append(up_nice_name)
                category.append('Reverse Osmosis')
                variable_list.append('Number Membranes')
                python_param.append('num_membranes')
                unit_list.append('-')

                value_list.append(fluxs[-1])
                python_var.append(unit_str)
                up_nice_name_list.append(up_nice_name)
                category.append('Reverse Osmosis')
                variable_list.append('Water Flux (m/s)')
                python_param.append('ro_recovery')
                unit_list.append('m/s')

                value_list.append(fluxs_lmh[-1])
                python_var.append(unit_str)
                up_nice_name_list.append(up_nice_name)
                category.append('Reverse Osmosis')
                variable_list.append('Water Flux (LMH)')
                python_param.append('flux_lmh')
                unit_list.append('LMH')

                value_list.append(kws[-1])
                python_var.append(unit_str)
                up_nice_name_list.append(up_nice_name)
                category.append('Reverse Osmosis')
                variable_list.append('Water Permeability Coeff.')
                python_param.append('a')
                unit_list.append('m/(bar.h)')

                value_list.append(kss[-1])
                python_var.append(unit_str)
                up_nice_name_list.append(up_nice_name)
                category.append('Reverse Osmosis')
                variable_list.append('Salt Permeability Coeff.')
                python_param.append('b')
                unit_list.append('m/hr')

            for conc in generate_constituent_list.run(m.fs):
                constituent, units = get_constituent_nice_name(conc)

                ### MASS IN KG PER M3
                value_list.append(value(getattr(m.fs, unit_str).conc_mass_in[0, conc]))
                python_var.append(unit_str)
                up_nice_name_list.append(up_nice_name)
                category.append('Inlet Constituent Density')
                variable_list.append(constituent)
                python_param.append(conc)
                unit_list.append(units)

                value_list.append(value(getattr(m.fs, unit_str).conc_mass_out[0, conc]))
                python_var.append(unit_str)
                up_nice_name_list.append(up_nice_name)
                category.append('Outlet Constituent Density')
                variable_list.append(constituent)
                python_param.append(conc)
                unit_list.append(units)

                value_list.append(value(getattr(m.fs, unit_str).conc_mass_waste[0, conc]))
                python_var.append(unit_str)
                up_nice_name_list.append(up_nice_name)
                category.append('Waste Constituent Density')
                variable_list.append(constituent)
                python_param.append(conc)
                unit_list.append(units)

                ### MASS IN KG --> MULTIPLIED BY FLOW
                value_list.append(value(getattr(m.fs, unit_str).conc_mass_in[0, conc]) *
                                  value(getattr(m.fs, unit_str).flow_vol_in[0]))
                python_var.append(unit_str)
                up_nice_name_list.append(up_nice_name)
                category.append('Inlet Constituent Total Mass')
                variable_list.append(constituent)
                python_param.append(conc)
                unit_list.append('kg')

                value_list.append(value(getattr(m.fs, unit_str).conc_mass_out[0, conc]) *
                                  value(getattr(m.fs, unit_str).flow_vol_out[0]))
                python_var.append(unit_str)
                up_nice_name_list.append(up_nice_name)
                category.append('Outlet Constituent Total Mass')
                variable_list.append(constituent)
                python_param.append(conc)
                unit_list.append('kg')

                value_list.append(value(getattr(m.fs, unit_str).conc_mass_waste[0, conc]) *
                                  value(getattr(m.fs, unit_str).flow_vol_waste[0]))
                python_var.append(unit_str)
                up_nice_name_list.append(up_nice_name)
                category.append('Waste Constituent Total Mass')
                variable_list.append(constituent)
                python_param.append(conc)
                unit_list.append('kg')

## FOR CALCULATING SYSTEM RO PARAMETERS

    # if len(pressures) > 1:
    #     ro_sys_flow_out = sum(flow_outs_ro)
    #     ro_sys_flow_in = sum(flow_ins_ro)
    #     ro_sys_flow_waste = ro_sys_flow_in - ro_sys_flow_out
    #     ro_sys_recovery = ro_sys_flow_out / ro_sys_flow_in * 100
    #     ro_sys_area = sum(areas)
    #     ro_sys_mems = sum(num_mems)
    #     ro_sys_flux = (ro_sys_flow_out / ro_sys_area) * (pyunits.meter / pyunits.sec)
    #     ro_sys_flux_lmh = pyunits.convert(ro_sys_flux,
    #                                       to_units=(pyunits.liter / pyunits.m ** 2 / pyunits.hour))
    #     ro_avg_press = sum(pressures) / len(pressures)
    #
    #     value_list.append(ro_avg_press)
    #     python_var.append('ro_system')
    #     up_nice_name_list.append('RO System')
    #     category.append('Reverse Osmosis')
    #     variable_list.append('RO System Avg. Pressure')
    #     python_param.append('ro_avg_press')
    #     unit_list.append('bar')
    #
    #     value_list.append(ro_sys_recovery)
    #     python_var.append('ro_system')
    #     up_nice_name_list.append('RO System')
    #     category.append('Reverse Osmosis')
    #     variable_list.append('RO System Recovery')
    #     python_param.append('ro_sys_recovery')
    #     unit_list.append('%')
    #
    #     value_list.append(ro_sys_area)
    #     python_var.append('ro_system')
    #     up_nice_name_list.append('RO System')
    #     category.append('Reverse Osmosis')
    #     variable_list.append('Total Membrane Area')
    #     python_param.append('ro_sys_area')
    #     unit_list.append('m2')
    #
    #     value_list.append(ro_sys_mems)
    #     python_var.append('ro_system')
    #     up_nice_name_list.append('RO System')
    #     category.append('Reverse Osmosis')
    #     variable_list.append('Total Number Membranes')
    #     python_param.append('ro_sys_mems')
    #     unit_list.append('-')
    #
    #     value_list.append(ro_sys_flux())
    #     python_var.append('ro_system')
    #     up_nice_name_list.append('RO System')
    #     category.append('Reverse Osmosis')
    #     variable_list.append('Water Flux (m/s)')
    #     python_param.append('ro_sys_flux')
    #     unit_list.append('m/s')
    #
    #     value_list.append(ro_sys_flux_lmh())
    #     python_var.append('ro_system')
    #     up_nice_name_list.append('RO System')
    #     category.append('Reverse Osmosis')
    #     variable_list.append('Water Flux (LMH)')
    #     python_param.append('ro_sys_flux_lmh')
    #     unit_list.append('LMH')
    #
    #     value_list.append(ro_sys_flow_in)
    #     python_var.append('ro_system')
    #     up_nice_name_list.append('RO System')
    #     category.append('Reverse Osmosis')
    #     variable_list.append('Total Flow In')
    #     python_param.append('ro_sys_flow_in')
    #     unit_list.append('m3/s')
    #
    #     value_list.append(ro_sys_flow_out)
    #     python_var.append('ro_system')
    #     up_nice_name_list.append('RO System')
    #     category.append('Reverse Osmosis')
    #     variable_list.append('Total Flow Out')
    #     python_param.append('ro_sys_flow_out')
    #     unit_list.append('m3/s')
    #
    #     value_list.append(ro_sys_flow_waste)
    #     python_var.append('ro_system')
    #     up_nice_name_list.append('RO System')
    #     category.append('Reverse Osmosis')
    #     variable_list.append('Total Flow Waste')
    #     python_param.append('ro_sys_flow_waste')
    #     unit_list.append('m3/s')

    df = pd.DataFrame()
    df['Unit Process Name'] = up_nice_name_list
    df['Variable'] = variable_list
    df['Value'] = value_list
    df['Metric'] = category
    df['Unit'] = unit_list
    df['python_var'] = python_var
    df['python_param'] = python_param
    df['Case Study'] = np.array(case_study)
    df['Scenario'] = np.array(scenario)
    df['Metric'] = np.where(df.Unit == '$MM/yr', 'Annual Cost', df.Metric)
    df['Metric'] = np.where(df.Unit == '$/m3', 'LCOW', df.Metric)
    if save is True:
        df.to_csv('results/case_studies/%s_%s.csv' % (case_study, scenario), index=False)

    return df


def combine_case_study_results(case_study=None, save=True):
    final_df = pd.DataFrame()
    keyword = ('%s_' % case_study)
    for fname in os.listdir('./results/case_studies'):
        if keyword in fname:
            df = pd.read_csv('./results/case_studies/%s' % fname)

        final_df = pd.concat([final_df, df])

    if save is True:
        final_df.to_csv('%s_all_scenarios' % case_study)

    return final_df


def compare_with_excel(excel_path, python_path):
    excel = pd.read_excel(excel_path)
    excel['Source'] = 'excel'

    py = pd.read_csv(python_path)
    py.rename(columns={
            'Unit Process Name': 'Unit_Process',
            'Case Study': 'Case_Study'
            }, inplace=True)
    py['Source'] = 'python'

    both = pd.concat([excel, py])
    pivot = pd.pivot_table(both, values='Value',
                           index=['Case_Study', 'Scenario', 'Unit_Process', 'Variable', 'Unit'],
                           columns=['Source']).reset_index()

    pivot.to_csv('results/check_with_excel.csv', index=False)

    return pivot