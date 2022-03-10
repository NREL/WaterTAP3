import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

__all__ = ['epa_cost_curve',
           'basic_unit']


def epa_cost_curve(unit_process, **kwargs):
    df = pd.read_csv('data/epa_cost_curves.csv', index_col='unit_process')
    df = df.loc[unit_process]

    params = ['flow_in', 'cap_total', 'electricity_intensity', 'tds_in', 'num_stage', 'radon_rem', 'ebct']

    def power(x, a, b):
        return a * x ** b

    if kwargs:
        temp = list(dict(**kwargs).items())[0]
        k, v = temp[0], temp[1]

        if k == 'tds_in':

            if unit_process == 'cation_exchange':
                if v >= 1000:
                    df = df[df.tds_in == 1000]
                elif v < 1000 and v >= 600:
                    df = df[df.tds_in == 600]
                else:
                    df = df[df.tds_in == 200]
            elif unit_process == 'anion_exchange':
                if v >= 150:
                    df = df[df.tds_in == 150]
                elif v < 150 and v >= 100:
                    df = df[df.tds_in == 100]
                else:
                    df = df[df.tds_in == 50]

        if k == 'radon_rem':

            if v >= 0.9:
                df = df[df.radon_rem == 0.99]
            else:
                df = df[df.radon_rem == 0.9]

        if k == 'ebct':

            if v > 30:
                df = df[df.ebct == 60]
            else:
                df = df[df.ebct == 30]

    df.dropna(axis=1, inplace=True)
    cols = df.columns
    mats_name = [c for c in cols if c not in params]
    mats_cost = {}
    for mat in mats_name:
        mats_cost[mat] = np.mean(df[mat])
    x = df.flow_in.to_list()
    y_cost = df.cap_total.to_list()
    y_elect = df.electricity_intensity.to_list()

    cost, _ = curve_fit(power, x, y_cost)
    elect, _ = curve_fit(power, x, y_elect)

    return cost, elect, mats_name, mats_cost, df


def basic_unit(unit_process, case_specific=None):
    if case_specific == 'solaire':
        df = pd.read_csv('data/basic_units_solaire.csv', index_col='unit_process')
    else:
        df = pd.read_csv('data/basic_unit_cost_curves_and_energy_intensities.csv', index_col='unit_process')
    df = df.loc[unit_process]
    flow_basis = df.flow_basis
    cap_basis = df.cap_basis
    cap_exp = df.cap_exp
    elect = df.electricity_intensity
    year = df.year
    kind = df.kind
    return flow_basis, cap_basis, cap_exp, elect, year, kind