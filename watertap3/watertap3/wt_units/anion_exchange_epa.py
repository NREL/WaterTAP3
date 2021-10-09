import pandas as pd
from pyomo.environ import Block, Constraint, Expression, NonNegativeReals, Var, exp, log, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'anion_exchange_epa'
basis_year = 2012
tpec_or_tic = 'TIC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self):
        t = self.flowsheet().config.time.first()
        def anion_ex_cost_curves(eqn, x):
            cost_df = pd.read_csv('data/an_ex_cost_eqns.csv', index_col='eqn')
            cost_df.drop(columns=['pct_deviation', 'date_modified', 'r_squared', 'max_size', 'min_size'], inplace=True)
            coeffs = dict(cost_df.loc[eqn].items())
            cost = coeffs['C1'] * x ** coeffs['C2'] + coeffs['C3'] * log(x) + coeffs['C4'] + coeffs['C5'] * exp(coeffs['C6'] * x) + coeffs['C7'] * x ** 3 + coeffs['C8'] * x ** 2 + coeffs[
                'C9'] * x + coeffs['C10']
            return cost

        ### VESSEL COST ###
        self.pv_ss_cost = anion_ex_cost_curves('ss_pv_eq', (80 * 7.48))  # cost of stainless steel pressure vessel
        self.pv_cs_cost = anion_ex_cost_curves('cs_pv_eq', (80 * 7.48))  # cost of carbon steel pressure vessels with stainless internals
        self.pv_csp_cost = anion_ex_cost_curves('csp_pv_eq', (80 * 7.48))  # cost of carbon steel pressure vessels with plastic internals
        self.pv_fg_cost = anion_ex_cost_curves('fg_pv_eq', (80 * 7.48))  # cost of fiberglass pressure vessels
        if self.pv_material == 'stainless':
            pv_cost = self.pv_ss_cost * self.tot_tanks
        if self.pv_material == 'carbon with stainless':
            pv_cost = self.pv_cs_cost * self.tot_tanks
        if self.pv_material == 'carbon with plastic':
            pv_cost = self.pv_csp_cost * self.tot_tanks
        if self.pv_material == 'fiberglass':
            pv_cost = self.pv_fg_cost * self.tot_tanks
        #             resin_type_list = ['styrenic_gel_1', 'styrenic_gel_2', 'styrenic_macro_1', 'styrenic_macro_2', 'polyacrylic', 'nitrate']

        ### RESIN COST ##
        # Cost taken from 'Cost Data' tab of 'wbs-anion-123017.xlsx'
        # look up table = sba_res_cost_cl
        self.resin_cap = (self.anion_resin_volume[t] * self.resin_cost[t]) + (self.cation_resin_volume[t] * self.resin_cost[t])

        ### BACKWASH TANKS ###
        # bw_ss_cost = anion_ex_cost_curves('st_bwt_eq', back_tank_vol)
        # bw_fg_cost = anion_ex_cost_curves('fg_bwt_eq', back_tank_vol)
        # bw_hdpe_cost = anion_ex_cost_curves('hdpe_bwt_eq', back_tank_vol)
        # if bw_tank_type == 'stainless':
        #     bw_tank_cost = bw_ss_cost * self.back_tanks
        # if bw_tank_type == 'fiberglass':
        #     bw_tank_cost = bw_fg_cost * self.back_tanks
        # if bw_tank_type == 'hdpe':
        #     bw_tank_cost = bw_hdpe_cost * self.back_tanks

        ix_cost = pv_cost + self.resin_cap

        return ix_cost * 1E-6 * self.tpec_tic

    def elect(self):  # m3/hr
        t = self.flowsheet().config.time.first()
        self.pump_power = (self.flow_vol_in[t] * 2 * 1E5) / 0.8  # w 2 bar pressure and 80% pump efficiency
        electricity = (self.pump_power * 1E-3) / (self.flow_vol_in[t] * 3600)  # kwh/m3
        return electricity

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        time = self.flowsheet().config.time
        t = self.flowsheet().config.time.first()
        flow_in = pyunits.convert(self.flow_vol_in[t], to_units=pyunits.m ** 3 / pyunits.hr)
        self.del_component(self.recovery_equation)
        try:
            self.freund1 = unit_params['freund1']  # Kf (ug/g)(L/ug)1/n
            self.freund2 = unit_params['freund2']  # dimensionless
            self.conc_in = unit_params['conc_in']
            self.conc_breakthru = unit_params['conc_breakthru']
            self.ph_in = unit_params['ph_in']
            self.ph_out = unit_params['ph_out']
        except:
            # defaults to values for nitrate removal using polystyrenic gel-type resin and 99% reduction (1 mg/L --> 0.01 mg/L)
            self.freund1 = 21.87
            self.freund2 = 3.04
            self.conc_in = 10
            self.conc_breakthru = 0.1
            self.ph_in = 7
            self.ph_out = 8.2

        try:
            self.geom = unit_params['geom']
            self.pv_material = unit_params['pv_material']
            self.bw_tank_type = unit_params['bw_tank_type']
            self.resin_name = unit_params['resin_type']
        except:
            self.geom = 'vertical'
            self.pv_material = 'stainless'
            self.bw_tank_type = 'stainless'
            self.resin_name = 'styrenic_gel_2'

        self.resin_type_list = ['styrenic_gel_1', 'styrenic_gel_2', 'styrenic_macro_1', 'styrenic_macro_2', 'polyacrylic', 'nitrate', 'custom']

        self.resin_dict = {
                'styrenic_gel_1': 148,
                'styrenic_gel_2': 173,
                'styrenic_macro_1': 207,
                'styrenic_macro_2': 221,
                'polyacrylic': 245,
                'nitrate': 173
                }

        flow_waste_gal_day = pyunits.convert(self.flow_vol_waste[t], to_units=pyunits.gallons / pyunits.day)
        flow_in_gal_day = pyunits.convert(self.flow_vol_in[t], to_units=pyunits.gallons / pyunits.day)
        flow_out_gal_day = pyunits.convert(self.flow_vol_out[t], to_units=pyunits.gallons / pyunits.day)
        tank_size = 80  # ft3

        self.anion_res_capacity = Var(time, initialize=10, domain=NonNegativeReals, doc='anion exchange resin capacity')  # anion exchange capacity -- kgr/ft3
        self.cation_res_capacity = Var(time,initialize=10, domain=NonNegativeReals, doc='cation exchange resin capacity')  # cation exchange capacity -- kgr/ft3
        self.mass_removed = Var(time, initialize=70, domain=NonNegativeReals, doc='mass removed')
        self.rinse_volume = Var(time, initialize=70, domain=NonNegativeReals, doc='rinse volume for anion exchange resin')  # gal/ft3 resin
        self.anion_resin_volume = Var(time, initialize=10, domain=NonNegativeReals, doc='anion exchange resin volume')  # ft3
        self.cation_resin_volume = Var(time, initialize=10, domain=NonNegativeReals, doc='cation exchange resin volume')  # ft3
        self.anion_rinse_flow = Var(time, initialize=10, domain=NonNegativeReals, doc='anion exchange rinse flow')  # gal/day
        self.anion_rinse_solids = Var(time, initialize=10, domain=NonNegativeReals, doc='additional cations from anion rinse volume')
        self.an_vol_per_unit = Var(time, initialize=10, domain=NonNegativeReals, doc='additional cations from anion rinse volume')  # anion exchange resin per unit
        self.cat_vol_per_unit = Var(time, initialize=10, domain=NonNegativeReals, doc='additional cations from anion rinse volume')  # cation exchange resin per unit
        self.num_ix_units_op = Var(time, initialize=3, domain=NonNegativeReals, doc='number of IX operating units')  ## NEEDS TO BE IN INTEGERS operational units
        self.num_ix_units_tot = Var(time, initialize=3, domain=NonNegativeReals, doc='number of IX total units')  ## NEEDS TO BE IN INTEGERS total units (op - 1)
        self.loading_rate = Var(time, initialize=5, doc='loading rate')  # gpm/ft2
        self.an_load_per_unit = Var(time, initialize=5, doc='an loading rate')
        self.cat_load_per_unit = Var(time, initialize=5, doc='cat loading rate')
        self.an_tank_diam = Var(time, initialize=5, doc='an tank diam')
        self.an_tank_depth = Var(time, initialize=5, doc='tank depth')
        self.cat_tank_diam = Var(time, initialize=5, doc='cat tank diam')
        self.cat_tank_depth = Var(time, initialize=5, doc='tank depth')
        self.anion_res_capacity.fix(16)
        self.cation_res_capacity.fix(18)
        self.rinse_volume.fix(70)
        self.num_ix_units_op.fix(3)
        self.loading_rate.fix(5)

        self.water_recovery_constraint = Constraint(
                expr=self.water_recovery[t] * flow_in_gal_day == flow_out_gal_day)
        self.removal_fraction[t, 'tds'].fix(0.9)

        self.mass_removed_constr = Constraint(
                expr=self.mass_removed[t] * 1000 == (((self.conc_mass_in[t, 'tds'] * self.removal_fraction[t, 'tds']
                                                       * 1E3 * 0.0548)) / 17.12) * flow_out_gal_day)  # mass removed kgr/day
        self.an_res_vol_constr = Constraint(expr=self.anion_resin_volume[t] * self.anion_res_capacity[t] == self.mass_removed[t])  # ft3/day
        self.cation_res_vol_constr = Constraint(expr=self.cation_resin_volume[t] * self.cation_res_capacity[t] == self.mass_removed[t] + self.anion_rinse_solids[t])  # ft3/day
        self.an_rins_vol_constr = Constraint(expr=flow_waste_gal_day == self.anion_resin_volume[t] * self.rinse_volume[t])  # gal/day
        self.an_rinse_solids_constr = Constraint(expr=self.anion_rinse_solids[t] == flow_waste_gal_day * (self.mass_removed[t] / 100) / 1000)  # Kgr/day

        self.num_cat_tanks = self.cation_resin_volume[t] / 80
        self.num_an_tanks = self.anion_resin_volume[t] / 80
        self.tot_tanks = self.num_an_tanks + self.num_cat_tanks
        self.resin_cost = Var(time, initialize=100, domain=NonNegativeReals, bounds=(0, 500), doc='lookupvalue')
        self.resin_cost.fix(self.resin_dict[self.resin_name])
        sys_specs = self.parent_block().costing_param
        # kg/yr replacement is every 4 days
        naoh_dose = 5.3 / 1000  # 5.3 #mg/l to kg/m3 (kg needed per m3 of inlet flow)
        nacl_dose1 = (8 * (self.cation_resin_volume[t] + self.anion_resin_volume[t]) * 0.453592)  # kg needed per day of replacement
        nacl_dose2 = nacl_dose1 * (365 / 4)  # kg required per year
        unknown_factor = 0.8
        nacl_dose3 = (nacl_dose2 / (self.flow_vol_in[t] * 3600 * 24 * 365)) * 0.8  # kg required per m3 of inlet water

        chem_dict = {'Sodium_Hydroxide_(NaOH)': naoh_dose, 'Sodium_Chloride': nacl_dose3}
        self.chem_dict = chem_dict

        # resin replacement assumption -> 4.5% of volume.
        resin_replacement = 0.045
        resin_life = 7

        # media/resin density 43 lb/ft3
        self.resin_loss_replacement = (self.cation_resin_volume[t] + self.anion_resin_volume[t]) * resin_replacement

        self.complete_bed_replacement = (self.cation_resin_volume[t] + self.anion_resin_volume[t] -
                                         self.resin_loss_replacement) / 7

        self.other_var_cost = self.resin_cost[t] * (self.complete_bed_replacement + self.resin_loss_replacement) * sys_specs.plant_cap_utilization * 1e-6

        self.costing.other_var_cost = self.other_var_cost

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')  # $M
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')  # kwh/m3
        financials.get_complete_costing(self.costing)