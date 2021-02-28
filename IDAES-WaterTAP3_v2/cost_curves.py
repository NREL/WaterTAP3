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
			else:
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
	a, b = cost[0], cost[1]

	return cost, elect, mats_name, mats_cost, df
