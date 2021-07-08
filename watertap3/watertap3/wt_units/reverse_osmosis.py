from pyomo.environ import Block, Constraint, Expression, NonNegativeReals, Var, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

module_name = 'reverse_osmosis'
basis_year = 2007
tpec_or_tic = 'TIC'

class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, t, b_cost):
        '''

        :param t: Indexing variable for Pyomo Var()
        :type t: int
        :param b_cost: Costing block for unit.
        :type b_cost: object
        :return: Fixed capital costs for reverse osmosis [$MM]
        '''
        ro_cap = (self.tpec_tic * (b_cost.pump_capital_cost + b_cost.mem_capital_cost + b_cost.erd_capital_cost) +
                  3.3 * (self.pressure_vessel_cost1[t] + self.rack_support_cost1[t])) * 1E-6  # $MM ### 1.65 is TIC
        return ro_cap

    def elect(self, t):
        '''

        :param t: Indexing variable for Pyomo Var()
        :type t: int
        :return:
        '''
        electricity = ((self.pump_power - self.erd_power) / 1000) / (self.flow_vol_in[t] * 3600)
        return electricity

    def _set_flow_mass(self, b, time):
        b.mass_flow_H2O = Var(time,
                              domain=NonNegativeReals,
                              units=self.units_meta('mass') / self.units_meta('time'),
                              doc='mass flow rate')
        b.mass_flow_tds = Var(time,
                              domain=NonNegativeReals,
                              units=self.units_meta('mass') / self.units_meta('time'),
                              doc='mass flow rate')

    def _set_mass_frac(self, b, time):
        b.mass_frac_H2O = Var(time,
                              units=pyunits.dimensionless,
                              doc='mass_fraction')
        b.mass_frac_tds = Var(time,
                              units=pyunits.dimensionless,
                              doc='mass_fraction')

    def _set_pressure_osm(self, b, time):
        b.pressure_osm = Var(time,
                             domain=NonNegativeReals,
                             doc='Osmotic pressure')

    def _set_osm_coeff(self, b, time):
        b.osm_coeff = Var(time,
                          initialize=0.1,
                          units=pyunits.dimensionless,
                          doc='Osmotic pressure coefficient')

    def _set_conc_mass(self, b, time):
        b.conc_mass_H2O = Var(time,
                              domain=NonNegativeReals,
                              units=self.units_meta('mass') / self.units_meta('volume'),
                              doc='H2O mass density')
        b.conc_mass_total = Var(time,
                                domain=NonNegativeReals,
                                units=self.units_meta('mass') / self.units_meta('volume'),
                                doc='density')

    def _set_pressure(self, b, time):
        b.pressure = Var(time,
                         initialize=45,
                         domain=NonNegativeReals,
                         bounds=(2, 90),
                         doc='pressure')

    def _set_constraints(self, t):
        ## FEED CONSTRAINTS
        self.feed.eq1 = Constraint(
                expr=self.feed.conc_mass_total[t] == 0.6312 * self.conc_mass_in[t, 'tds'] + 997.86)
        self.feed.eq2 = Constraint(
                expr=self.feed.conc_mass_H2O[t] == self.feed.conc_mass_total[t] - self.conc_mass_in[t, 'tds'])
        self.feed.eq3 = Constraint(
                expr=self.feed.mass_flow_H2O[t] == self.feed.conc_mass_H2O[t] * self.flow_vol_in[t])
        self.feed.eq4 = Constraint(
                expr=self.feed.mass_flow_tds[t] == self.conc_mass_in[t, 'tds'] * self.flow_vol_in[t])
        self.feed.eq5 = Constraint(
                expr=self.feed.mass_frac_tds[t] * (self.feed.mass_flow_H2O[t] + self.feed.mass_flow_tds[t]) == self.feed.mass_flow_tds[t])
        self.feed.eq6 = Constraint(
                expr=self.feed.mass_frac_H2O[t] == 1 - self.feed.mass_frac_tds[t])
        self.feed.eq7 = Constraint(
                expr=self.feed.osm_coeff[t] == 4.92 * self.feed.mass_frac_tds[t] ** 2 + self.feed.mass_frac_tds[t] * 0.0889 + 0.918)
        self.feed.eq8 = Constraint(
                expr=self.feed.pressure_osm[t] * 1e5 * (1 - self.feed.mass_frac_tds[t]) == 8.45e7 * self.feed.osm_coeff[t] * self.feed.mass_frac_tds[t])

        ## FLUX CONSTRAINTS
        self.water_salt_perm_eq1 = Constraint(
                expr=self.b[t] <= (0.083 * self.a[t] - 0.002) * 1.25)
        self.water_salt_perm_eq2 = Constraint(
                expr=self.b[t] >= (0.083 * self.a[t] - 0.002) * 0.75)

        ## RETENTATE CONSTRAINTS
        self.retentate.eq1 = Constraint(
                expr=self.retentate.conc_mass_total[t] == 0.6312 * self.conc_mass_waste[t, 'tds'] + 997.86)
        self.retentate.eq2 = Constraint(
                expr=self.retentate.conc_mass_H2O[t] == self.retentate.conc_mass_total[t] - self.conc_mass_waste[t, 'tds'])
        self.retentate.eq3 = Constraint(
                expr=self.retentate.mass_frac_tds[t] * self.retentate.conc_mass_total[t] == self.conc_mass_waste[t, 'tds'])
        self.retentate.eq4 = Constraint(
                expr=self.retentate.mass_frac_H2O[t] == 1 - self.retentate.mass_frac_tds[t])
        self.retentate.eq5 = Constraint(
                expr=self.retentate.osm_coeff[t] == 4.92 * self.retentate.mass_frac_tds[t] ** 2 + self.retentate.mass_frac_tds[t] * 0.0889 + 0.918)
        self.retentate.eq6 = Constraint(
                expr=self.retentate.pressure_osm[t] * 1E5 * (1 - self.retentate.mass_frac_tds[t]) == 8.45E7 * self.retentate.osm_coeff[t] * self.retentate.mass_frac_tds[t])

        ## PERMEATE CONSTRAINTS
        self.permeate.eq1 = Constraint(
                expr=self.permeate.conc_mass_total[t] == 756 * self.permeate.mass_frac_tds[t] * 1E-6 + 995)
        self.permeate.eq2 = Constraint(
                expr=self.conc_mass_out[t, 'tds'] == self.permeate.conc_mass_total[t] * self.permeate.mass_frac_tds[t] * 1E-6)
        self.permeate.eq3 = Constraint(
                expr=self.permeate.mass_flow_H2O[t] == self.membrane_area[t] * self.pure_water_flux[t])
        self.permeate.eq4 = Constraint(
                expr=self.permeate.mass_flow_tds[t] == 0.5 * self.membrane_area[t] * self.b[t] * 1E-7 * (self.conc_mass_in[t, 'tds'] + self.conc_mass_waste[t, 'tds']))
        self.permeate.eq5 = Constraint(
                expr=self.permeate.mass_frac_tds[t] * (self.permeate.mass_flow_tds[t] + self.permeate.mass_flow_H2O[t]) == 1E6 * self.permeate.mass_flow_tds[t])
        self.permeate.eq6 = Constraint(
                expr=self.pure_water_flux[t] == self.pw * self.a[t] * 1E-7 * ((self.feed.pressure[t] - self.p_atm - self.pressure_drop * 0.5) -
                        (self.feed.pressure_osm[t] + self.retentate.pressure_osm[t]) * 0.5))

        # PRESSURE BALANCE
        self.momentum_balance_eq = Constraint(
                expr=self.retentate.pressure[t] == self.feed.pressure[t] - self.pressure_drop)
        self.flow_vol_eq1 = Constraint(
                expr=self.flow_vol_out[t] * self.permeate.conc_mass_total[t] == (self.permeate.mass_flow_tds[t] + self.permeate.mass_flow_H2O[t]))
        self.flow_vol_eq2 = Constraint(
                expr=self.flow_vol_waste[t] * self.retentate.conc_mass_total[t] == (self.retentate.mass_flow_tds[t] + self.retentate.mass_flow_H2O[t]))
        self.pressure_waste_outlet_eq = Constraint(
                expr=self.feed.pressure[t] - self.pressure_drop == self.pressure_waste[t])

        # MASS BALANCE
        self.mass_balance_H2O = Constraint(
                expr=self.feed.mass_flow_H2O[t] == self.permeate.mass_flow_H2O[t] + self.retentate.mass_flow_H2O[t])
        self.mass_balance_tds = Constraint(
                expr=self.feed.mass_flow_tds[t] == self.permeate.mass_flow_tds[t] + self.retentate.mass_flow_tds[t])

        # PERMEATE PRESSURE
        self.p_out_eq = Constraint(
                expr=1 == self.pressure_out[t])
        self.pump_constraint_power = Constraint(
                expr=self.pump_power >= 0)

        # VESSEL COST
        self.pressure_vessel_cost1_eq = Constraint(
                expr=self.pressure_vessel_cost1[t] * 0.99 <= self.membrane_area[t] * 0.025 * 1000)  # assumes 2 trains. 150 ft start, 5ft per additional vessel. EPA.
        self.rack_support_cost1_eq = Constraint(
                expr=self.rack_support_cost1[t] * 0.99 <= (150 + (self.membrane_area[t] * 0.025 * 5)) * 33 * 2)
        self.pressure_vessel_cost1_eq2 = Constraint(
                expr=self.pressure_vessel_cost1[t] * 1.01 >= self.membrane_area[t] * 0.025 * 1000)  # assumes 2 trains. 150 ft start, 5ft per additional vessel. EPA.
        self.rack_support_cost1_eq2 = Constraint(
                expr=self.rack_support_cost1[t] * 1.01 >= (150 + (self.membrane_area[t] * 0.025 * 5)) * 33 * 2)

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        t = self.flowsheet().config.time.first()
        time = self.flowsheet().config.time
        sys_cost_params = self.parent_block().costing_param

        self.del_component(self.outlet_pressure_constraint)
        self.del_component(self.waste_pressure_constraint)
        self.del_component(self.recovery_equation)
        self.del_component(self.flow_balance)
        self.del_component(self.component_removal_equation)

        self.deltaP_waste.unfix()
        self.deltaP_outlet.unfix()

        self.permeate = Block()
        self.feed = Block()
        self.retentate = Block()

        self.units_meta = self.config.property_package.get_metadata().get_derived_units

        # DEFINE VARIABLES
        self.feed.water_flux = Var(time,
                                   initialize=5E-3,
                                   bounds=(1E-5, 1.5E-2),
                                   units=self.units_meta('mass') * self.units_meta('length') ** -2 * self.units_meta('time') ** -1,
                                   domain=NonNegativeReals,
                                   doc='water flux')
        self.retentate.water_flux = Var(time,
                                        initialize=5E-3,
                                        bounds=(1E-5, 1.5E-2),
                                        units=self.units_meta('mass') * self.units_meta('length') ** -2 * self.units_meta('time') ** -1,
                                        domain=NonNegativeReals,
                                        doc='water flux')
        self.pure_water_flux = Var(time,
                                   initialize=5E-3,
                                   bounds=(1E-3, 1.5E-2),
                                   units=self.units_meta('mass') * self.units_meta('length') ** -2 * self.units_meta('time') ** -1,
                                   domain=NonNegativeReals,
                                   doc='water flux')
        self.a = Var(time,
                     initialize=4.2,
                     bounds=(1, 9),
                     domain=NonNegativeReals,
                     doc='water permeability')
        self.b = Var(time,
                     initialize=0.35,
                     bounds=(0.1, 0.9),
                     domain=NonNegativeReals,
                     doc='Salt permeability')
        self.mem_cost = Var(time,
                            initialize=40,
                            bounds=(10, 80),
                            domain=NonNegativeReals,
                            doc='Membrane cost')
        self.membrane_area = Var(time,
                                 initialize=1E5,
                                 domain=NonNegativeReals,
                                 bounds=(1E1, 1E12),
                                 doc='area')
        self.factor_membrane_replacement = Var(time,
                                               initialize=0.2,
                                               domain=NonNegativeReals,
                                               bounds=(0.01, 3),
                                               doc='replacement rate membrane fraction')
        self.pressure_vessel_cost1 = Var(time,
                                         domain=NonNegativeReals)
        self.rack_support_cost1 = Var(time,
                                      domain=NonNegativeReals)
        self.factor_membrane_replacement.fix(0.25)  #

        # from excel regression based on paper for membrane cost y = 0.1285x - 0.0452 #R² =
        # 0.9932. y = b. x = a.
        # same 4 membranes used for regression ŷ = 15.04895X1 - 131.08641X2 + 29.43797

        for b in [self.permeate, self.feed, self.retentate]:
            self._set_flow_mass(b, time)
            self._set_mass_frac(b, time)
            self._set_conc_mass(b, time)
            self._set_osm_coeff(b, time)
            self._set_pressure_osm(b, time)
            if str(b) == 'permeate':
                continue
            else:
                self._set_pressure(b, time)

        self.feed.pressure.unfix()
        self.mem_cost.fix(30)
        self.a.fix(4.2)
        self.b.fix(0.35)
        self.const_list2 = list(self.config.property_package.component_list)
        self.const_list2.remove('tds')

        ## CONSTANTS
        self.pump_eff = 0.8
        self.erd_eff = 0.9
        self.pressure_drop = 3
        self.p_atm = 1
        self.pw = 1000

        self.pressure_diff = (self.feed.pressure[t] - self.pressure_in[t]) * 1E5  # assumes atm pressure before pump. change to Pa
        self.pump_power = (self.flow_vol_in[t] * self.pressure_diff) / self.pump_eff

        self._set_constraints(t)

        flow_in_m3hr = pyunits.convert(self.flow_vol_in[t],
                                       to_units=pyunits.m ** 3 / pyunits.hour)
        flow_waste_m3hr = pyunits.convert(self.flow_vol_waste[t],
                                          to_units=pyunits.m ** 3 / pyunits.hour)

        try:
            scaling = unit_params['scaling']

        except:
            scaling = 'no'

        for j in self.const_list2:
            if scaling == 'yes':
                self.del_component(self.component_mass_balance)
                setattr(self, ('%s_eq1' % j), Constraint(
                        expr=self.flow_vol_in[t] * self.conc_mass_in[t, j] == self.flow_vol_out[t] *
                             self.conc_mass_out[t, j] + self.flow_vol_waste[t] * self.conc_mass_waste[t, j]))

                setattr(self, ('%s_eq' % j), Constraint(
                        expr=self.removal_fraction[t, j] * self.flow_vol_in[t] * self.conc_mass_in[t, j] == self.flow_vol_waste[t] * self.conc_mass_waste[t, j]))

            else:
                setattr(self, ('%s_eq' % j), Constraint(
                        expr=self.removal_fraction[t, j] * flow_in_m3hr *
                             pyunits.convert(self.conc_mass_in[t, j],
                                             to_units=pyunits.mg / pyunits.liter) == flow_waste_m3hr *
                             pyunits.convert(self.conc_mass_waste[t, j],
                                             to_units=pyunits.mg / pyunits.liter)))

        b_cost = self.costing
        b_cost.pump_capital_cost = self.pump_power * (53 / 1E5 * 3600) ** 0.97
        b_cost.pressure_vessel_cap_cost1 = self.pressure_vessel_cost1[t] + self.rack_support_cost1[t]

        ################ Energy Recovery
        # assumes atmospheric pressure out
        if unit_params['erd'] == 'yes':
            x_value = (self.retentate.mass_flow_tds[t] + self.retentate.mass_flow_H2O[t]) / self.retentate.conc_mass_total[t] * 3600
            b_cost.erd_capital_cost = 3134.7 * (x_value * self.retentate.conc_mass_total[t]) ** 0.58
            self.erd_power = (self.flow_vol_waste[t] * (self.retentate.pressure[t] - 1) * 1E5) / self.erd_eff

        if unit_params['erd'] == 'no':
            self.erd_power = 0

        b_cost.erd_capital_cost = 0
        b_cost.mem_capital_cost = self.mem_cost[t] * self.membrane_area[t]

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(t, b_cost),
                                                           doc='Unadjusted fixed capital investment')

        self.num_membranes = self.membrane_area[t] / 37.161  # 400 ft2 / membrane = 37.161 m2 / membrane from BRACKISH paper
        self.ro_recovery = self.flow_vol_out[t] / self.flow_vol_in[t]
        self.flux = self.flow_vol_out[t] / (self.membrane_area[t] * pyunits.m ** 2)
        self.flux_lmh = pyunits.convert(self.flux,
                                        to_units=(pyunits.liter / pyunits.m ** 2 / pyunits.hour))
        ################ operating
        # membrane operating cost
        b_cost.other_var_cost = self.factor_membrane_replacement[t] * self.mem_cost[t] * self.membrane_area[t] * sys_cost_params.plant_cap_utilization * 1E-6
        self.electricity = Expression(
                expr=self.elect(t),
                doc='Electricity intensity [kWh/m3]')
        ####### electricity and chems
        sys_specs = self.parent_block().costing_param
        self.electricity = ((self.pump_power - self.erd_power) / 1000) / (self.flow_vol_in[t] * 3600)
        b_cost.pump_electricity_cost = 1E-6 * (self.pump_power / 1000) * 365 * 24 * sys_specs.electricity_price
        b_cost.erd_electricity_sold = 1E-6 * (self.erd_power / 1000) * 365 * 24 * sys_specs.electricity_price
        b_cost.electricity_cost = (b_cost.pump_electricity_cost - b_cost.erd_electricity_sold) * sys_cost_params.plant_cap_utilization

        self.chem_dict = {'unit_cost': 0.01}

        financials.get_complete_costing(self.costing)