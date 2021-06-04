from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: Voutchkov (2018) figures 4.2 and 4.4

module_name = 'chemical_addition'
basis_year = 2007
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, unit_params):
        '''
        **"unit_params" are the unit parameters passed to the model from the input sheet as a Python dictionary.**

        **EXAMPLE: {'dose': 10}**

        Fixed capital for chemical addition is a function of chemical dose, chemical solution flow, and the number of units.

        :param chemical_name: Chemical name to be used.
        :type chemical_name: str
        :param dose: Dose of chemical [mg/L]
        :type dose: float
        :return: Chemical addition fixed capital cost [$MM]
        '''
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        self.number_of_units = 2
        # BASED OFF OF SULFURIC ACID ADDITION -KAS
        self.base_fixed_cap_cost = 900.97
        self.cap_scaling_exp = 0.6179
        chem_name = unit_params['chemical_name']
        self.dose = pyunits.convert(unit_params['dose'] * (pyunits.mg / pyunits.liter), to_units=(pyunits.kg / pyunits.m ** 3))  # kg/m3
        self.chem_dict = {chem_name: self.dose}
        source_cost = self.base_fixed_cap_cost * self.solution_vol_flow() ** self.cap_scaling_exp
        chem_cap = (source_cost * self.tpec_tic * self.number_of_units) * 1E-6
        return chem_cap

    def elect(self):  # m3/hr
        '''
        Electricity intensity for chemical additions is a function of lift height, pump efficiency, and motor efficiency.

        :return: Electricity intensity [kWh/m3]
        '''
        self.lift_height = 100 * pyunits.ft
        self.pump_eff = 0.9 * pyunits.dimensionless
        self.motor_eff = 0.9 * pyunits.dimensionless
        soln_vol_flow = pyunits.convert(self.solution_vol_flow(), to_units=(pyunits.gallon / pyunits.minute))
        electricity = (0.746 * soln_vol_flow * self.lift_height / (3960 * self.pump_eff * self.motor_eff)) / self.flow_in  # kWh/m3
        return electricity

    def solution_vol_flow(self):
        '''
        Determine chemical solution flow rate in gal / day

        :return: Chemical solution flow [gal/day]
        '''
        self.solution_density = 1000 * (pyunits.kg / pyunits.m ** 3)  # kg/m3
        chemical_rate = self.flow_in * self.dose  # kg/hr
        chemical_rate = pyunits.convert(chemical_rate, to_units=(pyunits.kg / pyunits.day))
        soln_vol_flow = chemical_rate / self.solution_density
        soln_vol_flow = pyunits.convert(soln_vol_flow, to_units=(pyunits.gallon / pyunits.day))
        return soln_vol_flow  # gal/day

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