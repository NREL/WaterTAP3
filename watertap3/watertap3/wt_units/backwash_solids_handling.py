from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# Based on costs for SOLIDS HANDLING - FIGURE 5.7.1
# Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura) (2008)
# DOI:10.1002/9780470260036
## ELECTRICITY:

module_name = 'backwash_solids_handling'
basis_year = 2007
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def get_costing(self, unit_params=None, year=None):
        self.costing = Block()
        self.costing.basis_year = basis_year
        sys_cost_params = self.parent_block().costing_param
        self.tpec_or_tic = tpec_or_tic
        if self.tpec_or_tic == 'TPEC':
            self.costing.tpec_tic = tpec_tic = sys_cost_params.tpec
        else:
            self.costing.tpec_tic = tpec_tic = sys_cost_params.tic

        '''
        We need a get_costing method here to provide a point to call the
        costing methods, but we call out to an external consting module
        for the actual calculations. This lets us easily swap in different
        methods if needed.

        Within IDAES, the year argument is used to set the initial value for
        the cost index when we build the model.
        '''

        time = self.flowsheet().config.time.first()

        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)

        base_fixed_cap_cost = 9.76
        cap_scaling_exp = 0.918

        self.conc_mass_tot = 0
        for constituent in self.config.property_package.component_list:
            self.conc_mass_tot += self.conc_mass_in[time, constituent]

        self.density = 0.6312 * self.conc_mass_tot + 997.86  # kg/m3 # assumption from Tim's reference (ask Ariel for Excel if needed)
        self.total_mass = total_mass = self.density * pyunits.convert(flow_in, to_units=(pyunits.m ** 3 / pyunits.hr))
        self.chem_dict = {}

        lift_height = 100 * pyunits.ft
        pump_eff = 0.9 * pyunits.dimensionless
        motor_eff = 0.9 * pyunits.dimensionless

        def fixed_cap(total_mass):  # TODO not based on flow, just have placeholder numbers for Carlsbad
            filter_backwash_pumping_cost = 186458
            surface_wash_system = 99941
            air_scour_system = 463853
            wash_water_surge_basins = 770643
            wash_water_storage_tank = 216770
            gravity_sludge_thickener = 94864
            sludge_dewatering_lagoons = 4173
            sand_drying_beds = 45801

            filter_backwash_pumping_cost_units = 2
            surface_wash_system_units = 2
            air_scour_system_units = 2
            wash_water_surge_basins_units = 1
            wash_water_storage_tank_units = 1
            gravity_sludge_thickener_units = 1
            sludge_dewatering_lagoons_units = 3
            sand_drying_beds_units = 6

            fc = filter_backwash_pumping_cost * filter_backwash_pumping_cost_units
            sc = surface_wash_system * surface_wash_system_units
            ac = air_scour_system * air_scour_system_units
            sb = wash_water_surge_basins * wash_water_surge_basins_units
            st = wash_water_storage_tank * wash_water_storage_tank_units
            gs = gravity_sludge_thickener * gravity_sludge_thickener_units
            sd = sludge_dewatering_lagoons * sludge_dewatering_lagoons_units
            db = sand_drying_beds * sand_drying_beds_units

            costs_list = [fc, sc, ac, sb, st, gs, sd, db]
            scaling_factor_list = [1.000, 1.000, 1.000, 0.751, 0.847, 1.305, 0.714, 0.875]  # ANNA CHANGE TO VARIABLES

            # base_fixed_cap_cost = sum(costs_list) * 1E-6 # $M
            # cap_scaling_exp = sum(x * y for x, y in zip(scaling_factor_list, costs_list)) / sum(costs_list)

            capacity_basis = 1577255  # m3/s to kg/hr - CONSTANT BASED ON ASSUMPTION OF 100MGD BASIS

            backwash_cap = base_fixed_cap_cost * (total_mass / capacity_basis) ** cap_scaling_exp

            return backwash_cap  # MM$

        def electricity(flow_in):
            flow_in_gpm = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.gallons / pyunits.minute)
            flow_in_m3hr = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hour)
            electricity = (0.746 * flow_in_gpm * lift_height / (3960 * pump_eff * motor_eff)) / flow_in_m3hr  # kWh/m3
            return electricity

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(total_mass),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = electricity(flow_in)  # kwh/m3

        financials.get_complete_costing(self.costing)