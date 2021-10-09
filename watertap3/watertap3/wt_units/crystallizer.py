from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL AND ELECTRICITY:
# Survey of High-Recovery and Zero Liquid Discharge Technologies for Water Utilities (2008).
# WateReuse Foundation
# https://www.waterboards.ca.gov/water_issues/programs/grants_loans/water_recycling/research/02_006a_01.pdf
# Regressions for capital and electricity developed from
# data in Table A2.1, Table A2.3
# Capital = f(TDS, recovery, flow)
# Electricity = f(TDS, recovery, flow)

module_name = 'crystallizer'
basis_year = 2007
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self):
        '''
        Fixed capital for crystallizer. 

        :param tds_in: TDS concentration in to crystallizer [mg/L]
        :type tds_in: float
        :param water_recovery: Water recovery for the crystallizer
        :type water_recovery: float
        :param flow_in: Water flow in to crystallizer [m3/hr]
        :type flow_in: float
        :return: Fixed capital cost for crystallizer [$MM]
        '''
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        self.tds_in = pyunits.convert(self.conc_mass_in[time, 'tds'], to_units=(pyunits.mg / pyunits.liter))
        self.wr = self.water_recovery[time]
        self.chem_dict = {}
        crystal_cap = 1.41 - self.tds_in * 7.11E-7 + self.wr * 1.45 + self.flow_in * 5.55E-1
        return crystal_cap

    def elect(self):
        '''
        Electricity intensity for crystallizer.

        :param tds_in: TDS concentration in to crystallizer [mg/L]
        :type tds_in: float
        :param water_recovery: Water recovery for the crystallizer
        :type water_recovery: float
        :param flow_in: Water flow in to crystallizer [m3/hr]
        :type flow_in: float
        :return: Electricity intensity [kWh/m3]
        '''
        electricity = 56.7 + self.tds_in * 1.83E-5 - self.wr * 9.47 - self.flow_in * 8.63E-4
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