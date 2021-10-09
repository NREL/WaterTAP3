from pyomo.environ import Block, Constraint, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL AND ELECTRICITY:
# Survey of High-Recovery and Zero Liquid Discharge Technologies for Water Utilities (2008).
# WateReuse Foundation
# https://www.waterboards.ca.gov/water_issues/programs/grants_loans/water_recycling/research/02_006a_01.pdf
# Regressions for capital and electricity developed from
# data in Table 5.1, Table A2.3
# Capital = f(TDS, recovery, flow)
# Electricity = f(TDS, recovery, flow)

module_name = 'brine_concentrator'
basis_year = 2007
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self):
        '''
        Fixed capital for brine concentrator.

        :param tds_in: TDS concentration in to brine concentrator [mg/L]
        :type tds_in: float
        :param water_recovery: Water recovery for the brine concentrator
        :type water_recovery: float
        :param flow_in: Water flow in to brine concentrator [m3/hr]
        :type flow_in: float
        :return: Fixed capital cost for brine concentrator [$MM]
        '''
        time = self.flowsheet().config.time.first()
        self.chem_dict = {}
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        self.tds_in = pyunits.convert(self.conc_mass_in[time, 'tds'], to_units=(pyunits.mg / pyunits.liter))
        bc_cap = 15.1 + (self.tds_in * 3.02E-4) - (self.water_recovery[time] * 18.8) + (self.flow_in * 8.08E-2)
        return bc_cap

    def elect(self):
        '''
        Electricity intensity for brine concentrator.

        :param tds_in: TDS concentration in to brine concentrator [mg/L]
        :type tds_in: float
        :param water_recovery: Water recovery for the brince concentrator
        :type water_recovery: float
        :param flow_in: Water flow in to brine concentrator [m3/hr]
        :type flow_in: float
        :return: Electricity intensity [kWh/m3]
        '''
        time = self.flowsheet().config.time.first()
        electricity = 9.73 + self.tds_in * 1.1E-4 + self.water_recovery[time] * 10.4 + self.flow_in * 3.83E-5
        return electricity

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')
        financials.get_complete_costing(self.costing)