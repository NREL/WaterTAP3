from pyomo.environ import Block, Constraint, Expression, NonNegativeReals, Var, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'reverse_osmosis'
basis_year = 2007
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, t, b_cost):
        ro_cap = (1.65 * (b_cost.pump_capital_cost + b_cost.mem_capital_cost + b_cost.erd_capital_cost)
                  + 3.3 * (self.pressure_vessel_cost1[t] + self.rack_support_cost1[t])) * 1E-6  # $MM ### 1.65 is TIC
        return ro_cap

    def elect(self, t):
        electricity = ((self.pump_power - self.erd_power) / 1000) / (self.flow_vol_in[t] * 3600)  # kwh/m3
        return electricity

    def _set_flow_mass(self, b):
        time = self.flowsheet().config.time
        b.mass_flow_h20 = Var(time,
                              # initialize=1000,
                              domain=NonNegativeReals,
                              units=self.units_meta('mass') / self.units_meta('time'),
                              doc='mass flow rate')

        b.mass_flow_tds = Var(time,
                              # initialize=50,
                              domain=NonNegativeReals,
                              units=self.units_meta('mass') / self.units_meta('time'),
                              doc='mass flow rate')

    def _set_mass_frac(self, b):
        time = self.flowsheet().config.time
        b.mass_frac_h20 = Var(time,
                              # initialize=0.75,
                              # domain=NonNegativeReals,
                              units=pyunits.dimensionless,
                              doc='mass_fraction')

        b.mass_frac_tds = Var(time,
                              # initialize=0.35,
                              # domain=NonNegativeReals,
                              units=pyunits.dimensionless,
                              doc='mass_fraction')

    def _set_pressure_osm(self, b):
        time = self.flowsheet().config.time
        b.pressure_osm = Var(time,
                             # initialize=20,
                             domain=NonNegativeReals,
                             # units=pyunits.dimensionless,
                             doc='Osmotic pressure')

    def _set_osm_coeff(self, b):
        time = self.flowsheet().config.time
        b.osm_coeff = Var(time,
                          initialize=0.1,
                          # domain=NonNegativeReals,
                          units=pyunits.dimensionless,
                          doc='Osmotic pressure coefficient')

    def _set_conc_mass(self, b):
        time = self.flowsheet().config.time
        b.conc_mass_h20 = Var(time,
                              # initialize=900,
                              domain=NonNegativeReals,
                              units=self.units_meta('mass') / self.units_meta('volume'),
                              doc='h20 mass density')

        b.conc_mass_total = Var(time,
                                # initialize=1000,
                                domain=NonNegativeReals,
                                units=self.units_meta('mass') / self.units_meta('volume'),
                                doc='density')

    def _set_pressure(self, b):
        time = self.flowsheet().config.time
        b.pressure = Var(time,
                         initialize=45,
                         domain=NonNegativeReals,
                         bounds=(2, 90),
                         # units=pyunits.dimensionless,
                         doc='pressure')

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

        permeate = self.permeate
        feed = self.feed
        retentate = self.retentate

        self.units_meta = self.config.property_package.get_metadata().get_derived_units

        # DEFINE VARIABLES

        self.feed.water_flux = Var(time,
                                   initialize=5e-3,
                                   bounds=(1e-5, 1.5e-2),
                                   units=self.units_meta('mass') * self.units_meta('length') ** -2 * self.units_meta('time') ** -1,
                                   domain=NonNegativeReals,
                                   doc='water flux')

        self.retentate.water_flux = Var(time,
                                        initialize=5e-3,
                                        bounds=(1e-5, 1.5e-2),
                                        units=self.units_meta('mass') * self.units_meta('length') ** -2 * self.units_meta('time') ** -1,
                                        domain=NonNegativeReals,
                                        doc='water flux')

        self.pure_water_flux = Var(time,
                                   initialize=5e-3,
                                   bounds=(1e-3, 1.5e-2),
                                   units=self.units_meta('mass') * self.units_meta('length') ** -2 * self.units_meta('time') ** -1,
                                   domain=NonNegativeReals,
                                   doc='water flux')

        self.a = Var(time,
                     initialize=4.2,
                     bounds=(1, 9),
                     # units=units_meta('mass')/units_meta('area')**-2*units_meta('time')**-1,
                     domain=NonNegativeReals,
                     doc='water permeability')

        self.b = Var(time,
                     initialize=0.35,
                     bounds=(0.1, 0.9),
                     # units=units_meta('mass')*units_meta('length')**-2*units_meta('time')**-1,
                     domain=NonNegativeReals,
                     doc='Salt permeability')

        self.mem_cost = Var(time,
                            initialize=40,
                            bounds=(10, 80),
                            # units=units_meta('mass')*units_meta('length')**-2*units_meta('time')**-1,
                            domain=NonNegativeReals,
                            doc='Membrane cost')

        self.membrane_area = Var(time,
                                 initialize=1e5,
                                 domain=NonNegativeReals,
                                 bounds=(1e1, 1e12),
                                 # units=units_meta('mass')/units_meta('time'),
                                 doc='area')

        self.factor_membrane_replacement = Var(time,
                                               initialize=0.2,
                                               domain=NonNegativeReals,
                                               bounds=(0.01, 3),
                                               doc='replacement rate membrane fraction')

        self.factor_membrane_replacement.fix(0.25)  #
        # from excel regression based on paper for membrane cost y = 0.1285x - 0.0452 #R² = 0.9932. y = b. x = a.
        self.water_salt_perm_eq1 = Constraint(
                expr=self.b[t] <= (0.083 * self.a[t] - 0.002) * 1.25
                )

        self.water_salt_perm_eq2 = Constraint(
                expr=self.b[t] >= (0.083 * self.a[t] - 0.002) * 0.75
                )

        self.mem_cost.fix(30)
        # same 4 membranes used for regression ŷ = 15.04895X1 - 131.08641X2 + 29.43797

        for b in [permeate, feed, retentate]:
            self._set_flow_mass(b)
            self._set_mass_frac(b)
            self._set_conc_mass(b)
            self._set_osm_coeff(b)
            self._set_pressure_osm(b)
            if str(b) == 'permeate':
                continue
            else:
                self._set_pressure(b)
        feed.pressure.unfix()

        self.a.fix(4.2)
        self.b.fix(0.35)

        self.const_list2 = list(self.config.property_package.component_list)  # .remove("tds")
        self.const_list2.remove("tds")

        flow_in_m3hr = pyunits.convert(self.flow_vol_in[t], to_units=pyunits.m ** 3 / pyunits.hour)
        flow_waste_m3hr = pyunits.convert(self.flow_vol_waste[t], to_units=pyunits.m ** 3 / pyunits.hour)

        # if "stage" in unit_params:
        try:
            scaling = unit_params['scaling']

        except:
            scaling = 'no'

        for j in self.const_list2:
            if scaling == 'yes':
                self.del_component(self.component_mass_balance)
                setattr(self, ("%s_eq1" % j), Constraint(expr=self.flow_vol_in[t] * self.conc_mass_in[t, j] ==
                                                              self.flow_vol_out[t] * self.conc_mass_out[t, j] +
                                                              self.flow_vol_waste[t] * self.conc_mass_waste[t, j]))
                # if j in ['toc', 'sulfur', 'nitrate_as_nitrogen']:
                setattr(self, ("%s_eq" % j), Constraint(
                        expr=self.removal_fraction[t, j] * self.flow_vol_in[t] * self.conc_mass_in[t, j]
                             == self.flow_vol_waste[t] * self.conc_mass_waste[t, j]
                        ))

            else:
                setattr(self, ("%s_eq" % j), Constraint(
                        expr=self.removal_fraction[t, j] * flow_in_m3hr *
                             pyunits.convert(self.conc_mass_in[t, j], to_units=pyunits.mg / pyunits.liter)
                             == flow_waste_m3hr * pyunits.convert(self.conc_mass_waste[t, j], to_units=pyunits.mg / pyunits.liter)
                        ))

        ## CONSTANTS
        pump_eff = 0.8  # efficiency of pump
        erd_eff = 0.9
        mem_cost = 35  # ~30 dollars for 2007 converted to 2020 and from Optimum design of reverse osmosis system under different feed concentration and product specification
        pump_cost = 53 / 1e5 * 3600  # $ per W
        pressure_drop = 3  # bar Typical pressure drops range from 0.1-3 bar.
        a = 4.2e-7  # water permeability coefficient m bar-1 s-1
        b_constant = 0.35e-7  # Salt permeability coefficient m s-1
        p_atm = 1  # bar atmospheric pressure
        pw = 1000  # density of water kg/m3

        # area per vessel 40m2 of membrane area -> from EPA cost model
        mem_area_per_vessel = 40
        # cost per vessel is assumed as 1000 so same source as pump cost. EPA is 783 but then adds other associated costs.
        cost_per_vessel = 1000

        ## FEED CONSTRAINTS
        feed.eq1 = Constraint(
                expr=feed.conc_mass_total[t] == 0.6312 * self.conc_mass_in[t, 'tds'] + 997.86  # kg/m3
                )

        feed.eq2 = Constraint(
                expr=feed.conc_mass_h20[t] == feed.conc_mass_total[t] - self.conc_mass_in[t, 'tds']  # kg/m3
                )

        feed.eq3 = Constraint(
                expr=feed.mass_flow_h20[t] == feed.conc_mass_h20[t] * self.flow_vol_in[t]  # kg/s
                )
        feed.eq4 = Constraint(
                expr=feed.mass_flow_tds[t] == self.conc_mass_in[t, 'tds'] * self.flow_vol_in[t]  # kg/s
                )
        feed.eq5 = Constraint(
                expr=feed.mass_frac_tds[t] * (feed.mass_flow_h20[t] + feed.mass_flow_tds[t])
                     == feed.mass_flow_tds[t]
                )
        feed.eq6 = Constraint(
                expr=feed.mass_frac_h20[t] == 1 - feed.mass_frac_tds[t]
                )
        feed.eq7 = Constraint(
                expr=feed.osm_coeff[t] == 4.92 * feed.mass_frac_tds[t] ** 2 + feed.mass_frac_tds[t] * 0.0889 + 0.918  # unitless
                )
        feed.eq8 = Constraint(
                expr=feed.pressure_osm[t] * 1e5 * (1 - feed.mass_frac_tds[t])
                     == 8.45e7 * feed.osm_coeff[t] * feed.mass_frac_tds[t]  # bar
                )

        ## RETENTATE CONSTRAINTS
        retentate.eq2 = Constraint(
                expr=retentate.conc_mass_total[t] == 0.6312 * self.conc_mass_waste[t, 'tds'] + 997.86  # kg/m3
                )

        retentate.eq3 = Constraint(
                expr=retentate.conc_mass_h20[t] == retentate.conc_mass_total[t] - self.conc_mass_waste[t, 'tds']  # kg/m3
                )

        retentate.eq6 = Constraint(
                expr=retentate.mass_frac_tds[t] * retentate.conc_mass_total[t] == self.conc_mass_waste[t, 'tds']
                )
        retentate.eq7 = Constraint(
                expr=retentate.mass_frac_h20[t] == 1 - retentate.mass_frac_tds[t]
                )
        retentate.eq8 = Constraint(
                expr=retentate.osm_coeff[t] == 4.92 * retentate.mass_frac_tds[t] ** 2
                     + retentate.mass_frac_tds[t] * 0.0889 + 0.918  # unitless
                )
        retentate.eq9 = Constraint(
                expr=retentate.pressure_osm[t] * 1e5 * (1 - retentate.mass_frac_tds[t])
                     == 8.45e7 * retentate.osm_coeff[t] * retentate.mass_frac_tds[t]  # bar
                )

        ## PERMEATE CONSTRAINTS
        permeate.eq1 = Constraint(
                expr=permeate.conc_mass_total[t] == 756 * permeate.mass_frac_tds[t] * 1e-6 + 995
                )
        permeate.eq2 = Constraint(
                expr=self.conc_mass_out[t, 'tds'] == permeate.conc_mass_total[t] * permeate.mass_frac_tds[t] * 1e-6
                )

        permeate.eq3 = Constraint(
                expr=permeate.mass_flow_h20[t] == self.membrane_area[t] * self.pure_water_flux[t]
                )

        permeate.eq4 = Constraint(
                expr=permeate.mass_flow_tds[t] == 0.5 * self.membrane_area[t]
                     * self.b[t] * 1e-7 * (self.conc_mass_in[t, 'tds'] + self.conc_mass_waste[t, 'tds'])
                )
        permeate.eq5 = Constraint(
                expr=permeate.mass_frac_tds[t] * (permeate.mass_flow_tds[t] + permeate.mass_flow_h20[t])
                     == 1e6 * permeate.mass_flow_tds[t]
                )

        permeate.eq33 = Constraint(
                expr=self.pure_water_flux[t] == pw * self.a[t] * 1e-7 * ((feed.pressure[t] - p_atm - pressure_drop * 0.5)
                                                                         - (feed.pressure_osm[t] + retentate.pressure_osm[t]) * 0.5)
                )

        # momentum (pressure) balance
        self.momentum_balance_eq = Constraint(
                expr=retentate.pressure[t] == feed.pressure[t] - pressure_drop)

        self.flow_vol_eq1 = Constraint(
                expr=self.flow_vol_out[t] * permeate.conc_mass_total[t] ==
                     (permeate.mass_flow_tds[t] + permeate.mass_flow_h20[t])
                )

        self.flow_vol_eq2 = Constraint(
                expr=self.flow_vol_waste[t] * retentate.conc_mass_total[t] == (retentate.mass_flow_tds[t] + retentate.mass_flow_h20[t])
                )

        ########################################################################
        ########################################################################

        # Mass balances
        self.mass_balance_h20 = Constraint(
                expr=feed.mass_flow_h20[t] == permeate.mass_flow_h20[t] + retentate.mass_flow_h20[t]
                )

        self.mass_balance_tds = Constraint(
                expr=feed.mass_flow_tds[t] == permeate.mass_flow_tds[t] + retentate.mass_flow_tds[t]
                )

        ########################################################################
        ########################################################################

        self.pressure_waste_outlet_eq = Constraint(
                expr=self.feed.pressure[t] - pressure_drop == self.pressure_waste[t]
                )

        # permeate pressure
        self.p_out_eq = Constraint(
                expr=1 == self.pressure_out[t]
                )

        b_cost = self.costing

        self.pressure_diff = (feed.pressure[t] - self.pressure_in[t]) * 1E5  # assumes atm pressure before pump. change to Pa
        self.pump_power = (self.flow_vol_in[t] * self.pressure_diff) / pump_eff  # W
        b_cost.pump_capital_cost = self.pump_power * (53 / 1E5 * 3600)  ** 0.97 #


        self.pump_constraint_power = Constraint(
                expr=self.pump_power >= 0
                )

        # vessel cost
        # self.number_of_vessels = self.membrane_area[t] * 0.025

        self.pressure_vessel_cost1 = Var(time, domain=NonNegativeReals)
        self.rack_support_cost1 = Var(time, domain=NonNegativeReals)

        self.pressure_vessel_cost1_eq = Constraint(
                expr=self.pressure_vessel_cost1[t] * 0.99 <= self.membrane_area[t] * 0.025 * 1000)
        # assumes 2 trains. 150 ft start, 5ft per additional vessel. EPA.
        self.rack_support_cost1_eq = Constraint(
                expr=self.rack_support_cost1[t] * 0.99 <= (150 + (self.membrane_area[t] * 0.025 * 5)) * 33 * 2)

        self.pressure_vessel_cost1_eq2 = Constraint(
                expr=self.pressure_vessel_cost1[t] * 1.01 >= self.membrane_area[t] * 0.025 * 1000)
        # assumes 2 trains. 150 ft start, 5ft per additional vessel. EPA.
        self.rack_support_cost1_eq2 = Constraint(
                expr=self.rack_support_cost1[t] * 1.01 >= (150 + (self.membrane_area[t] * 0.025 * 5)) * 33 * 2)

        b_cost.pressure_vessel_cap_cost1 = self.pressure_vessel_cost1[t] + self.rack_support_cost1[t]

        ################ Energy Recovery
        # assumes atmospheric pressure out
        if unit_params['erd'] == 'yes':
            x_value = (retentate.mass_flow_tds[t] + retentate.mass_flow_h20[t]) / retentate.conc_mass_total[t] * 3600
            b_cost.erd_capital_cost = 3134.7 * (x_value * retentate.conc_mass_total[t]) ** 0.58
            self.erd_power = (self.flow_vol_waste[t] * (retentate.pressure[t] - 1) * 1E5) / erd_eff

        if unit_params['erd'] == 'no':
            self.erd_power = 0
        b_cost.erd_capital_cost = 0

        b_cost.mem_capital_cost = self.mem_cost[t] * self.membrane_area[t]

        # total capital investment
        # b_cost.fixed_cap_inv_unadjusted = fixed_cap_mcgiv(self.flow_vol_out[t] *3600)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(t, b_cost),
                                                           doc='Unadjusted fixed capital investment')  # $M
        ################ operating
        # membrane operating cost
        b_cost.other_var_cost = self.factor_membrane_replacement[t] * self.mem_cost[t] * self.membrane_area[t] * sys_cost_params.plant_cap_utilization * 1e-6
        self.electricity = Expression(expr=self.elect(t),
                                      doc='Electricity intensity [kwh/m3]')  # kwh/m3
        ####### electricity and chems
        sys_specs = self.parent_block().costing_param
        self.electricity = ((self.pump_power - self.erd_power) / 1000) / (self.flow_vol_in[t] * 3600)  # kwh/m3
        b_cost.pump_electricity_cost = 1e-6 * (self.pump_power / 1000) * 365 * 24 * sys_specs.electricity_price  # $MM/yr
        b_cost.erd_electricity_sold = 1e-6 * (self.erd_power / 1000) * 365 * 24 * sys_specs.electricity_price  # $MM/yr
        b_cost.electricity_cost = (b_cost.pump_electricity_cost - b_cost.erd_electricity_sold) * sys_cost_params.plant_cap_utilization

        self.chem_dict = {'unit_cost': 0.01}

        financials.get_complete_costing(self.costing)