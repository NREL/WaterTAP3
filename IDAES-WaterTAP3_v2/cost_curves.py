import pandas as pd
import numpy as np
from scipy.optimize import curve_fit


def cost_curve(unit_process, **kwargs):
    df = pd.read_csv('data/cost_curves.csv', index_col='unit_process')
    df = df.loc[unit_process]

    params = ['flow_in_mgd', 'flow_in', 'flow_in_avg_mgd', 'flow_in_avg', 'cap_direct', 'cap_other', 'cap_indirect', 'cap_total', 'labor', 'materials', 'other', 'electricity_annual',
              'electricity_flow', 'tds_in', 'num_stage', 'radon_rem', 'ebct']

    def power(x, a, b):
        return a * x ** b

    if kwargs:
        temp = list(dict(**kwargs).items())[0]
        k, v = temp[0], temp[1]

        if k == 'tds_in':
            # df = df[['flow_in', 'cap_total', 'electricity_flow', k]]
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
            # df = df[['flow_in', 'cap_total', 'electricity_flow', k]]
            if v >= 0.9:
                df = df[df.radon_rem == 0.99]
            else:
                df = df[df.radon_rem == 0.9]

        if k == 'ebct':
            # df = df[['flow_in', 'cap_total', 'electricity_flow', k]]
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
    y_elect = df.electricity_flow.to_list()

    cost, _ = curve_fit(power, x, y_cost)
    elect, _ = curve_fit(power, x, y_elect)

    return cost, elect, mats_name, mats_cost, df


def basic_unit(unit_process, case_specific=None):
    if case_specific == 'solaire':
        df = pd.read_csv('data/basic_units_solaire.csv', index_col='unit_process')
    else:
        df = pd.read_csv('data/basic_unit.csv', index_col='unit_process')
    df = df.loc[unit_process]
    flow_basis = df.flow_basis
    cap_basis = df.cap_basis
    cap_exp = df.cap_exp
    elect = df.elect
    year = df.year
    kind = df.kind
    return flow_basis, cap_basis, cap_exp, elect, year, kind

def evap_ratio_curve(air_temp, salinity, humidity, wind_speed):
    x0 = air_temp
    x1 = salinity
    x2 = humidity
    x3 = wind_speed
    return -0.0465233559 * (x0) - 0.0011189096 * (x1) - 0.7088094852 * (x2) - 0.0257883428 * (x3) + 0.0017209498 * (x0 ** 2) + 7.54344e-05 * (x0 * x1) + 0.0923261483 * (x0 * x2) - 0.0002522583 * (
                x0 * x3) + 7.74e-07 * (x1 ** 2) + 0.0012751516 * (x1 * x2) + 1.16276e-05 * (x1 * x3) - 0.042838386 * (x2 ** 2) + 0.0842127857 * (x2 * x3) + 0.0006828725 * (x3 ** 2) - 2.55508e-05 * (
                       x0 ** 3) - 1.6415e-06 * (x0 ** 2 * x1) - 0.001500322 * (x0 ** 2 * x2) + 4.46853e-05 * (x0 ** 2 * x3) + 2.8e-08 * (x0 * x1 ** 2) - 8.93471e-05 * (x0 * x1 * x2) - 2.6285e-06 * (
                       x0 * x1 * x3) - 0.0472354101 * (x0 * x2 ** 2) + 0.000814877 * (x0 * x2 * x3) - 0.0001268287 * (x0 * x3 ** 2) - 2.4e-09 * (x1 ** 3) + 1.9905e-06 * (x1 ** 2 * x2) - 1.214e-07 * (
                       x1 ** 2 * x3) - 0.0004983631 * (x1 * x2 ** 2) - 0.0002213007 * (x1 * x2 * x3) + 1.36134e-05 * (x1 * x3 ** 2) + 0.4822279076 * (x2 ** 3) - 0.0473877989 * (
                       x2 ** 2 * x3) - 0.0027941016 * (x2 * x3 ** 2) + 9.36662e-05 * (x3 ** 3) + 1.3159327466
