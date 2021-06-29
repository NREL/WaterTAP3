from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'electrodialysis_reversal'
basis_year = 2016
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self):
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        self.chem_dict = {}
        ed_cap = 31 * self.flow_in / 946  # $MM
        return ed_cap

    def elect(self):

        # EDR electricity intensity updated June 23, 2021
        # Correspondence with Cameron McKay on June 22, 2021
        # This regression was done in excel EDR_electricity.xlsx
        # Figure is from Membrane Technology and Applications, by Richard W. Baker and is citing the following source for this figure:
        # L.H. Shaffer and M.S. Mintz, Electrodialysis, in Principles of Desalination, K.S. Spiegler (ed.), Academic Press, New York, pp. 200-289 (1966).
        time = self.flowsheet().config.time.first()
        self.tds_in = pyunits.convert(self.conc_mass_in[time, 'tds'], to_units=(pyunits.mg / pyunits.L))
        ed_elect = 5.149E-4 * self.tds_in + 0.2534
        return ed_elect

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