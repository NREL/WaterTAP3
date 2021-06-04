import numpy as np
import pandas as pd
from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials, ml_regression
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: Texas Water Board

module_name = 'chlorination'
basis_year = 2014
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, unit_params):  # flow in mgd for this cost curve
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.Mgallons / pyunits.day)
        self.contact_time = 1.5  # hours
        self.contact_time_mins = 1.5 * 60  # min
        self.ct = 450  # mg/L-min
        self.chlorine_decay_rate = 3.0  # mg/Lh
        self.dose = self.chlorine_decay_rate * self.contact_time + self.ct / self.contact_time_mins
        chem_name = unit_params['chemical_name']
        self.chem_dict = {chem_name: self.dose * 1E-3}
        df = pd.read_csv('data/chlorine_dose_cost_twb.csv')
        new_dose_list = np.arange(0, 25.1, 0.5)
        cost_list = []
        flow_list = []
        dose_list = []
        for flow in df.Flow_mgd.unique():
            df_hold = df[df.Flow_mgd == flow]
            del df_hold['Flow_mgd']
            if 0 not in df_hold.Cost.values:
                xs = np.hstack((0, df_hold.Dose.values))  # dont think we need the 0s
                ys = np.hstack((0, df_hold.Cost.values))  # dont think we need the 0s
            else:
                xs = df_hold.Dose.values
                ys = df_hold.Cost.values
            a = ml_regression.get_cost_curve_coefs(xs=xs, ys=ys)[0][0]
            b = ml_regression.get_cost_curve_coefs(xs=xs, ys=ys)[0][1]
            for new_dose in new_dose_list:
                if new_dose in df.Dose:
                    if flow in df.Flow_mgd:
                        cost_list.append(df[((df.Dose == new_dose) & (df.Flow_mgd == flow))].Cost.max())
                    else:
                        cost_list.append(a * new_dose ** b)
                else:
                    cost_list.append(a * new_dose ** b)
                dose_list.append(new_dose)
                flow_list.append(flow)
        dose_cost_table = pd.DataFrame()
        dose_cost_table['flow_mgd'] = flow_list
        dose_cost_table['dose'] = dose_list
        dose_cost_table['cost'] = cost_list
        df1 = dose_cost_table[dose_cost_table.dose == self.dose]
        xs = np.hstack((0, df1.flow_mgd.values))
        ys = np.hstack((0, df1.cost.values))
        a = ml_regression.get_cost_curve_coefs(xs=xs, ys=ys)[0][0]
        b = ml_regression.get_cost_curve_coefs(xs=xs, ys=ys)[0][1]
        return (a * self.flow_in ** b) * 1E-3  # $MM

    def elect(self):
        electricity = 0.00005 # An Analysis of Energy Consumption and the Use of Renewables for a Small Drinking Water Treatment Plant
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