from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: from PML tab, for the kg/hr and not consistent with the usual flow rate cost curves TODO

module_name = 'surface_discharge'
basis_year = 2020
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, unit_params):
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=(pyunits.m ** 3 / pyunits.hr))
        self.chem_dict = {}
        self.conc_mass_tot = 0
        for constituent in self.config.property_package.component_list:
            self.conc_mass_tot += self.conc_mass_in[time, constituent]
        self.density = 0.6312 * self.conc_mass_tot + 997.86  # kg/m3 # assumption from Tim's reference (ask Ariel for Excel if needed)
        self.total_mass = self.density * self.flow_in  # kg/hr to tons for Mike's Excel needs
        self.base_fixed_cap_cost = 35
        self.cap_scaling_exp = 0.873
        self.capacity_basis = 10417  # m3/hr - from PML tab based on 250000 gallons per day
        self.pipe_cost_basis = 35000
        try:
            self.pipe_distance = unit_params['pipe_distance'] * pyunits.miles
            self.pipe_diameter = 8 * pyunits.inches
            self.pipe_fixed_cap_cost = (self.pipe_cost_basis * self.pipe_distance * self.pipe_diameter) * 1E-6
            surf_dis_cap = self.base_fixed_cap_cost * (self.flow_in / self.capacity_basis) ** self.cap_scaling_exp + self.pipe_fixed_cap_cost
            return surf_dis_cap
        except:
            surf_dis_cap = self.base_fixed_cap_cost * (self.flow_in / self.capacity_basis) ** self.cap_scaling_exp
            return surf_dis_cap  # M$

    def elect(self, unit_params):
        time = self.flowsheet().config.time.first()
        try:
            pump = unit_params['pump']
        except:
            pump = 'yes'
        self.lift_height = 100 * pyunits.ft
        self.pump_eff = 0.9 * pyunits.dimensionless
        self.motor_eff = 0.9 * pyunits.dimensionless
        if pump == 'yes':
            flow_in_gpm = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.gallons / pyunits.minute)
            electricity = (0.746 * flow_in_gpm * self.lift_height / (3960 * self.pump_eff * self.motor_eff)) / self.flow_in  # kWh/m3
            return electricity
        else:
            return 0

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(unit_params),
                                                           doc='Unadjusted fixed capital investment')  # $M
        self.electricity = Expression(expr=self.elect(unit_params),
                                      doc='Electricity intensity [kwh/m3]')  # kwh/m3
        financials.get_complete_costing(self.costing)