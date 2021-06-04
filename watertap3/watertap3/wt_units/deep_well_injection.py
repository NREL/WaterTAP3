from pyomo.environ import Block, Expression, NonNegativeReals, Var, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE:
## CAPITAL
# Developed from Kay Bailey and produced water case study data

module_name = 'deep_well_injection'
basis_year = 2011
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, unit_params):
        time = self.flowsheet().config.time
        t = self.flowsheet().config.time.first()
        self.lift_height = Var(time, initialize=400, domain=NonNegativeReals, units=pyunits.ft, doc='Lift height for pump [ft]')  # lift height in feet
        self.flow_in = pyunits.convert(self.flow_vol_in[t], to_units=pyunits.m ** 3 / pyunits.hr)
        try:
            self.lift_height.fix(unit_params['lift_height'])
        except:
            self.lift_height.fix(400)
        self.delta_pressure = self.lift_height[t] * 0.0299  # lift height converted to bar
        self.cap_scaling_exp = 0.7
        self.cap_scaling_val = 473.2
        self.well_pump_fixed_cap_cost = 16.9  # this is wells/pumps fixed capital AFTER applying TIC factor -- DOES NOT INCLUDE ANY PIPING
        self.pipe_cost_basis = 35000  # $ / (inch * mile) -- this value taken from produced water case studies in WT3 Excel model
        self.pipe_distance = unit_params['pipe_distance'] * pyunits.miles
        self.pipe_diameter = 8 * pyunits.inches
        self.chem_dict = {}
        self.pipe_fixed_cap_cost = (self.pipe_cost_basis * self.pipe_distance * self.pipe_diameter) * 1E-6
        self.tot_fixed_cap = self.well_pump_fixed_cap_cost + self.pipe_fixed_cap_cost
        cap_scaling_factor = self.flow_in / self.cap_scaling_val
        deep_well_cap = self.tot_fixed_cap * cap_scaling_factor ** self.cap_scaling_exp
        return deep_well_cap

    def elect(self):
        t = self.flowsheet().config.time.first()
        time = self.flowsheet().config.time
        self.pump_eff = 0.9
        self.motor_eff = 0.9
        flow_in_gpm = pyunits.convert(self.flow_in, to_units=(pyunits.gallon / pyunits.minute))
        electricity = (0.746 * flow_in_gpm * self.lift_height[t] / (3960 * self.pump_eff * self.motor_eff)) / self.flow_in
        return electricity

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(unit_params),
                                                           doc='Unadjusted fixed capital investment')  # $M
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')  # kwh/m3
        financials.get_complete_costing(self.costing)