import numpy as np
import pandas as pd
from pyomo.environ import Block, Expression, inequality, units as pyunits
from watertap3.utils import financials, ml_regression
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: 
# CAPITAL: Table 3.23 - User's Manual for Integrated Treatment Train Toolbox - Potable Reuse (IT3PR) Version 2.0

module_name = 'chlorination'
basis_year = 2014
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, unit_params):
        '''

        :param unit_params: Unit parameters from input sheet.
        :return:
        '''

        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.Mgallons / pyunits.day)
        try:
            self.contact_time = unit_params['contact_time'] * pyunits.hour
            self.contact_time_mins = pyunits.convert(self.contact_time, to_units=pyunits.minute)
            self.ct = unit_params['ct'] * ((pyunits.milligram * pyunits.minute)/ (pyunits.liter))
            self.chlorine_decay_rate = unit_params['chlorine_decay_rate'] * (pyunits.milligram / (pyunits.liter * pyunits.hour))
        except:
            self.contact_time = 1.5  * pyunits.hour
            self.contact_time_mins = pyunits.convert(self.contact_time, to_units=pyunits.minute)
            self.ct = 450 * ((pyunits.milligram * pyunits.minute)/ (pyunits.liter))
            self.chlorine_decay_rate = 3.0  * (pyunits.milligram / (pyunits.liter * pyunits.hour))
        try:
            self.dose = float(unit_params['dose'])
        except:
            self.dose = self.chlorine_decay_rate * self.contact_time + self.ct / self.contact_time_mins
            self.dose = float(self.dose())
        if self.dose > 25 or self.dose < 0.1:
            print(f'\n\t**ALERT**\n\tInput chlorine dose of {self.dose} mg/L is invalid.')
            print('\tCost curve valid only for chlorine dose 0.1 - 25 mg/L')
            if self.dose > 25:
                print('\tInput dose changed to 25 mg/L.\n')
                self.dose = 25
            if self.dose < 0.1:
                print('\tInput dose changed to 0.1 mg/L.\n')
                self.dose = 0.1
        try:
            self.chem_name = unit_params['chemical_name']
        except:
            self.chem_name = 'Chlorine'
        self.chem_dict = {self.chem_name: self.dose * 1E-3}
        self.df = df = pd.read_csv('data/chlorination_cost.csv')
        self.new_dose_list = new_dose_list = np.arange(0, 25.1, 0.1)
        self.cost_list = cost_list = []
        self.flow_list = flow_list = []
        self.dose_list = dose_list = []
        for flow in df.Flow_mgd.unique():
            self.df_hold = df_hold = df[df.Flow_mgd == flow]
            if 0 not in df_hold.Cost.values:
                xs = np.hstack((0, df_hold.Dose.values))
                ys = np.hstack((0, df_hold.Cost.values))
            else:
                xs = df_hold.Dose.values
                ys = df_hold.Cost.values
            a = ml_regression.get_cost_curve_coefs(xs=xs, ys=ys)[0][0]
            b = ml_regression.get_cost_curve_coefs(xs=xs, ys=ys)[0][1]
            for new_dose in new_dose_list:
                if new_dose in df.Dose.to_list():
                    if flow in df.Flow_mgd.to_list():
                        cost_list.append(df[((df.Dose == new_dose) & (df.Flow_mgd == flow))].Cost.max())
                    else:
                        cost_list.append(a * new_dose ** b)
                else:
                    cost_list.append(a * new_dose ** b)
                dose_list.append(new_dose)
                flow_list.append(flow)
        self.dose_cost_table = dose_cost_table = pd.DataFrame()
        dose_cost_table['flow_mgd'] = flow_list
        dose_cost_table['dose'] = dose_list
        dose_cost_table['cost'] = cost_list
        self.df1 = df1 = dose_cost_table[dose_cost_table.dose == self.dose]
        self.final_xs = np.hstack((0, df1.flow_mgd.values))
        self.final_ys = np.hstack((0, df1.cost.values))
        (self.final_a, self.final_b) = ml_regression.get_cost_curve_coefs(xs=self.final_xs, ys=self.final_ys)[0]
        self.cl_cap = (self.final_a * self.flow_in ** self.final_b) * 1E-3
        return self.cl_cap

    def elect(self):
        '''
        Electricity intensity.

        :return: Electricity intensity [kWh/m3]
        '''
        electricity = 0.00005
        return electricity

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(unit_params),
                                                           doc='Unadjusted fixed capital investment')
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')
        financials.get_complete_costing(self.costing)