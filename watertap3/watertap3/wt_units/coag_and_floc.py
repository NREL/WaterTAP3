from pyomo.environ import Block, Expression, Var, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'coag_and_floc'
basis_year = 2020
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, unit_params):
        '''

        :param unit_params:
        :return:
        '''
        time = self.flowsheet().config.time
        t = self.flowsheet().config.time.first()
        self.alum_dose = Var(time, initialize=10, units=pyunits.mg / pyunits.liter, doc='Alum dose [mg/L]')
        alum_dose_kgm3 = pyunits.convert(unit_params['alum_dose'] * (pyunits.mg / pyunits.liter), to_units=(pyunits.kg / pyunits.m ** 3))
        self.alum_dose.fix(alum_dose_kgm3)
        self.flow_in = pyunits.convert(self.flow_vol_in[t], to_units=pyunits.m ** 3 / pyunits.hr)
        self.polymer_dose = pyunits.convert(unit_params['polymer_dose'] * (pyunits.mg / pyunits.liter), to_units=(pyunits.kg / pyunits.m ** 3))
        self.an_polymer = self.polymer_dose / 2  # MIKE ASSUMPTION NEEDED
        self.cat_polymer = self.polymer_dose / 2  # MIKE ASSUMPTION NEEDE
        self.rapid_mixers = 1 * pyunits.dimensionless
        self.floc_mixers = 3 * pyunits.dimensionless
        self.rapid_mix_processes = 1 * pyunits.dimensionless
        self.floc_processes = 2 * pyunits.dimensionless
        self.coag_processes = 1 * pyunits.dimensionless
        self.floc_injection_processes = 1 * pyunits.dimensionless
        self.rapid_mix_retention_time = 5.5 * pyunits.seconds  # seconds (rapid mix)
        self.floc_retention_time = 12 * pyunits.minutes  # minutes
        self.chem_dict = {'Aluminum_Al2_SO4_3': alum_dose_kgm3, 'Anionic_Polymer': self.an_polymer, 'Cationic_Polymer': self.cat_polymer}
        flow_in_gpm = pyunits.convert(self.flow_in, to_units=pyunits.gallons / pyunits.minute)  # m3/hr to GPM
        rapid_mix_basin_volume = pyunits.convert(self.rapid_mix_retention_time, to_units=pyunits.minutes) * flow_in_gpm  # gallons
        floc_basin_volume = self.floc_retention_time * flow_in_gpm * 1E-6  # gallons
        alum_flow = alum_dose_kgm3 * self.flow_in  # kg / hr
        alum_flow = pyunits.convert(alum_flow, to_units=(pyunits.lb / pyunits.hour))  # lb / hr
        poly_flow = self.polymer_dose * self.flow_in  # kg / hr
        poly_flow = pyunits.convert(poly_flow, to_units=(pyunits.lb / pyunits.day))  # lb / hr
        rapid_mix_cap = (7.0814 * rapid_mix_basin_volume + 33269) * self.rapid_mix_processes  # $
        floc_cap = (952902 * floc_basin_volume + 177335) * self.floc_processes  # $
        coag_inj_cap = (212.32 * alum_flow + 73225) * self.coag_processes  # $
        floc_inj_cap = (13662 * poly_flow + 20861) * self.floc_injection_processes  # $
        coag_floc_cap = (rapid_mix_cap + floc_cap + coag_inj_cap + floc_inj_cap) * 1E-6 * self.tpec_tic
        return coag_floc_cap

    def elect(self):
        flow_in_gpm = pyunits.convert(self.flow_in, to_units=pyunits.gallons / pyunits.minute)  # MGD to GPM
        rapid_mix_basin_volume = pyunits.convert(self.rapid_mix_retention_time, to_units=pyunits.minutes) * flow_in_gpm
        rapid_mix_basin_volume = pyunits.convert(rapid_mix_basin_volume, to_units=pyunits.m ** 3)  # gallons to m3
        rapid_mix_power_consumption = (900 ** 2 * 0.001 * rapid_mix_basin_volume) * pyunits.watts  # W
        rapid_mix_power = rapid_mix_power_consumption * self.rapid_mixers * 1E-3  # kW
        floc_basin_volume = self.floc_retention_time * flow_in_gpm
        floc_basin_volume = pyunits.convert(floc_basin_volume, to_units=(pyunits.m ** 3))  # gallons to m3
        floc_power_consumption = (80 ** 2 * 0.001 * floc_basin_volume) * pyunits.watts  # W
        floc_mix_power = floc_power_consumption * self.floc_mixers * 1E-3  # kW
        total_power = (rapid_mix_power + floc_mix_power) / self.flow_in
        return total_power  # kWh/m3

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