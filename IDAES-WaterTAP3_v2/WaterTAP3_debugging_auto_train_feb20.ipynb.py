{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "metadata": {},
   "outputs": [],
   "source": [
    "import watertap as wt"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "metadata": {},
   "outputs": [],
   "source": [
    "from case_study_trains import *\n",
    "import case_study_trains"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "metadata": {},
   "outputs": [],
   "source": [
    "m = wt.watertap_setup(dynamic = False)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "metadata": {},
   "outputs": [],
   "source": [
    "wt.case_study_trains.train = {\"case_study\": \"Carlsbad\",\n",
    "                             \"reference\": \"NAWI\",\n",
    "                             \"scenario\": \"Baseline\"}"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 5,
   "metadata": {},
   "outputs": [],
   "source": [
    "# TODO LATER: how to make this sync with info in train input data. We might not need to do that.\n",
    "#But, if the source water type is different to what is in the train (pfd dictionary), \n",
    "#then we should updat the node name. If more than two sources - what to do? Needs to be\n",
    "#based on pfd node!?\n",
    "\n",
    "wt.case_study_trains.source_water = {\"case_study\": \"Carlsbad\", \n",
    "                             \"reference\": \"NAWI\",\n",
    "                             \"scenario\": \"Baseline\",\n",
    "                             \"water_type\": \"Seawater\"}"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "metadata": {},
   "outputs": [],
   "source": [
    "train1 = wt.case_study_trains.source_water"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 7,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Carlsbad\n"
     ]
    }
   ],
   "source": [
    "import generate_constituent_list\n",
    "import financials\n",
    "generate_constituent_list.train = train1\n",
    "generate_constituent_list.source_water = wt.case_study_trains.source_water\n",
    "\n",
    "financials.train = train1\n",
    "financials.source_water = wt.case_study_trains.source_water\n",
    "financials.get_system_specs(m.fs)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 8,
   "metadata": {},
   "outputs": [],
   "source": [
    "m.fs.water = WaterParameterBlock()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 9,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "['bromide', 'calcium', 'chloride', 'magnesium', 'potassium', 'sodium', 'strontium', 'sulfate', 'tds']\n"
     ]
    }
   ],
   "source": [
    "m = wt.design.add_water_source(m = m, source_name = \"source1\", link_to = None, \n",
    "                     reference = train1['reference'], water_type = train1['water_type'], \n",
    "                     case_study = train1['case_study']) # m3/s = 16500 m3/h = 104.6121 MGD = 4.5833 m3/s)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": 10,
   "metadata": {},
   "outputs": [],
   "source": [
    "m = wt.design.add_unit_process(m = m, \n",
    "                               unit_process_name = \"sulfuric_acid_addition\", \n",
    "                               unit_process_type = \"sulfuric_acid_addition\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 11,
   "metadata": {},
   "outputs": [],
   "source": [
    "m.fs.arc1 = Arc(source=m.fs.source1.outlet, \n",
    "                             destination=m.fs.sulfuric_acid_addition.inlet)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": 12,
   "metadata": {
    "scrolled": true
   },
   "outputs": [],
   "source": [
    "#m = wt.case_study_trains.get_case_study(m = m) # flow is set as case study flow unless defined."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": 13,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/html": [
       "\n",
       "        <iframe\n",
       "            width=\"100%\"\n",
       "            height=\"500px\"\n",
       "            src=\"tmp/example.html\"\n",
       "            frameborder=\"0\"\n",
       "            allowfullscreen\n",
       "        ></iframe>\n",
       "        "
      ],
      "text/plain": [
       "<IPython.lib.display.IFrame at 0x7f85a2415650>"
      ]
     },
     "execution_count": 13,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "wt.display.show_train2(model_name=m)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": 14,
   "metadata": {
    "scrolled": true
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "degrees_of_freedom: 0\n",
      "Ipopt 3.12.13: \n",
      "\n",
      "******************************************************************************\n",
      "This program contains Ipopt, a library for large-scale nonlinear optimization.\n",
      " Ipopt is released as open source code under the Eclipse Public License (EPL).\n",
      "         For more information visit http://projects.coin-or.org/Ipopt\n",
      "******************************************************************************\n",
      "\n",
      "This is Ipopt version 3.12.13, running with linear solver mumps.\n",
      "NOTE: Other linear solvers might be more efficient (see Ipopt documentation).\n",
      "\n",
      "Number of nonzeros in equality constraint Jacobian...:      170\n",
      "Number of nonzeros in inequality constraint Jacobian.:        0\n",
      "Number of nonzeros in Lagrangian Hessian.............:       45\n",
      "\n",
      "Total number of variables............................:       60\n",
      "                     variables with only lower bounds:        0\n",
      "                variables with lower and upper bounds:        0\n",
      "                     variables with only upper bounds:        0\n",
      "Total number of equality constraints.................:       60\n",
      "Total number of inequality constraints...............:        0\n",
      "        inequality constraints with only lower bounds:        0\n",
      "   inequality constraints with lower and upper bounds:        0\n",
      "        inequality constraints with only upper bounds:        0\n",
      "\n",
      "iter    objective    inf_pr   inf_du lg(mu)  ||d||  lg(rg) alpha_du alpha_pr  ls\n",
      "   0  0.0000000e+00 1.60e+05 0.00e+00  -1.0 0.00e+00    -  0.00e+00 0.00e+00   0\n",
      "   1  0.0000000e+00 6.35e+04 0.00e+00  -1.0 1.60e+05    -  1.00e+00 5.00e-01h  2\n",
      "   2  0.0000000e+00 8.53e+04 0.00e+00  -1.0 7.42e+04    -  1.00e+00 1.00e+00H  1\n",
      "   3  0.0000000e+00 9.58e+00 3.18e+04  -1.0 1.86e+04  -4.0 1.00e+00 1.00e+00h  1\n",
      "   4  0.0000000e+00 3.10e-03 1.03e+01  -1.0 8.03e+00    -  1.00e+00 1.00e+00h  1\n",
      "   5  0.0000000e+00 1.06e-07 8.25e-07  -1.0 3.88e-03  -4.5 1.00e+00 1.00e+00h  1\n",
      "   6  0.0000000e+00 8.73e-11 4.38e-11  -8.6 1.13e-03    -  1.00e+00 1.00e+00h  1\n",
      "Cannot recompute multipliers for feasibility problem.  Error in eq_mult_calculator\n",
      "\n",
      "Number of Iterations....: 6\n",
      "\n",
      "                                   (scaled)                 (unscaled)\n",
      "Objective...............:   0.0000000000000000e+00    0.0000000000000000e+00\n",
      "Dual infeasibility......:   4.3784489380479329e-11    4.3784489380479329e-11\n",
      "Constraint violation....:   8.7311491370201111e-11    8.7311491370201111e-11\n",
      "Complementarity.........:   0.0000000000000000e+00    0.0000000000000000e+00\n",
      "Overall NLP error.......:   8.7311491370201111e-11    8.7311491370201111e-11\n",
      "\n",
      "\n",
      "Number of objective function evaluations             = 10\n",
      "Number of objective gradient evaluations             = 7\n",
      "Number of equality constraint evaluations            = 10\n",
      "Number of inequality constraint evaluations          = 0\n",
      "Number of equality constraint Jacobian evaluations   = 7\n",
      "Number of inequality constraint Jacobian evaluations = 0\n",
      "Number of Lagrangian Hessian evaluations             = 6\n",
      "Total CPU secs in IPOPT (w/o function evaluations)   =      0.013\n",
      "Total CPU secs in NLP function evaluations           =      0.000\n",
      "\n",
      "EXIT: Optimal Solution Found.\n",
      "\b----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "fs.source1\n",
      "inlet : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 66.3, (0.0, 'calcium'): 409.6, (0.0, 'chloride'): 19162.0, (0.0, 'magnesium'): 1278.0, (0.0, 'potassium'): 395.3, (0.0, 'sodium'): 10679.0, (0.0, 'strontium'): 1.3, (0.0, 'sulfate'): 2680.0, (0.0, 'tds'): 35000.0}\n",
      "         :    flow_vol : {0.0: 4.5833}\n",
      "         :    pressure : {0.0: 200000.0}\n",
      "         : temperature : {0.0: 300}\n",
      "outlet : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 66.29999999999997, (0.0, 'calcium'): 409.5999999999998, (0.0, 'chloride'): 19161.999999999985, (0.0, 'magnesium'): 1277.9999999999993, (0.0, 'potassium'): 395.2999999999998, (0.0, 'sodium'): 10678.999999999993, (0.0, 'strontium'): 1.2999999999999994, (0.0, 'sulfate'): 2679.999999999998, (0.0, 'tds'): 34999.99999999998}\n",
      "         :    flow_vol : {0.0: 4.5833}\n",
      "         :    pressure : {0.0: 199999.9999}\n",
      "         : temperature : {0.0: 300.0}\n",
      "waste : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): -7.347724669080048e-06, (0.0, 'calcium'): -4.539408593676332e-05, (0.0, 'chloride'): -0.0021236363959749346, (0.0, 'magnesium'): -0.0001416348669587736, (0.0, 'potassium'): -4.3809282656460825e-05, (0.0, 'sodium'): -0.0011835044920024402, (0.0, 'strontium'): -1.4407339497747668e-07, (0.0, 'sulfate'): -0.00029701208367095556, (0.0, 'tds'): -0.003878889147963187}\n",
      "         :    flow_vol : {0.0: -4.910983208128146e-17}\n",
      "         :    pressure : {0.0: 199999.9999}\n",
      "         : temperature : {0.0: 300.0}\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "fs.sulfuric_acid_addition\n",
      "inlet : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 66.29999999999997, (0.0, 'calcium'): 409.5999999999998, (0.0, 'chloride'): 19161.999999999985, (0.0, 'magnesium'): 1277.9999999999993, (0.0, 'potassium'): 395.2999999999998, (0.0, 'sodium'): 10678.999999999993, (0.0, 'strontium'): 1.2999999999999994, (0.0, 'sulfate'): 2679.999999999998, (0.0, 'tds'): 34999.99999999998}\n",
      "         :    flow_vol : {0.0: 4.5833}\n",
      "         :    pressure : {0.0: 199999.9999}\n",
      "         : temperature : {0.0: 300.0}\n",
      "outlet : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 66.29999999999993, (0.0, 'calcium'): 409.59999999999957, (0.0, 'chloride'): 19161.999999999975, (0.0, 'magnesium'): 1277.9999999999984, (0.0, 'potassium'): 395.29999999999956, (0.0, 'sodium'): 10678.999999999987, (0.0, 'strontium'): 1.2999999999999987, (0.0, 'sulfate'): 2679.999999999997, (0.0, 'tds'): 34999.999999999956}\n",
      "         :    flow_vol : {0.0: 4.5833}\n",
      "         :    pressure : {0.0: 199999.9998}\n",
      "         : temperature : {0.0: 300.0}\n",
      "waste : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): -9.789671231534774e-07, (0.0, 'calcium'): -6.04803745005574e-06, (0.0, 'chloride'): -0.00028294065148501673, (0.0, 'magnesium'): -1.8870585285424026e-05, (0.0, 'potassium'): -5.836887710251785e-06, (0.0, 'sodium'): -0.00015768308206144587, (0.0, 'strontium'): -1.919557858998369e-08, (0.0, 'sulfate'): -3.957211921585519e-05, (0.0, 'tds'): -0.000516800062604964}\n",
      "         :    flow_vol : {0.0: 0.0}\n",
      "         :    pressure : {0.0: 199999.9998}\n",
      "         : temperature : {0.0: 300.0}\n",
      "total_cap_investment: 0.44123616005988775\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n"
     ]
    }
   ],
   "source": [
    "wt.run_water_tap(m = m, solver_results = True, print_model_results = True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {
    "scrolled": true
   },
   "outputs": [],
   "source": [
    "cost_range_list = []; #results will be inputted in this array\n",
    "#up_name = \"tri_media_filtration\" # which unit process it applies to. TODO hould be user input.\n",
    "\n",
    "#for value_change in pct_to_target1: # cycles through each value from MC range\n",
    "for value_change in [0.4, 0.8]: #, 0.9]:\n",
    "\n",
    "    # create and build model\n",
    "    m = wt.watertap_setup(dynamic = False)\n",
    "    m = wt.case_study_trains.get_case_study(name = 'carlsbad', flow = 4.5833, m = m)\n",
    "\n",
    "    m.fs.tri_media_filtration.water_recovery.fix(value_change)\n",
    "\n",
    "    # set variable to MC value\n",
    "    wt.run_water_tap(m)\n",
    "    results_table = get_results_table(m, unit_process_name)\n",
    "    cost_range_list.append(results_table.total_up_cost.sum())\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "cost_range_list"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "#### DO NOT USE THE BELOW ####"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import time\n",
    "from multiprocessing import Pool\n",
    "import multiprocessing\n",
    "\n",
    "mu = 0.6\n",
    "sigma = .1\n",
    "num_reps = 50\n",
    "\n",
    "input_list = np.random.normal(mu,sigma, size = num_reps) #, sigma, num_reps).round(4)\n",
    "\n",
    "count, bins, ignored = plt.hist(input_list, 25, density=True)\n",
    "plt.plot(bins, 1/(sigma * np.sqrt(2 * np.pi)) * np.exp( - (bins - mu)**2 / (2 * sigma**2) ),\n",
    "          linewidth=2, color='r')\n",
    "plt.show()\n",
    "\n",
    "### INPUT TO MODEL LIST: ### CAN BE AUTOMATED FOR USER TO LABEL THE VARIABLE. TOOD ###\n",
    "no_of_proc = 4\n",
    "list_final = []\n",
    "for i in range(no_of_proc):\n",
    "    part2 = len(input_list) / no_of_proc\n",
    "    i2 = ((i+1)*part2)\n",
    "    list1 = input_list[int(i*part2):int(i2)]\n",
    "    list_final.append(list1)\n",
    "    \n",
    "    \n",
    "def monte_run(list_final):\n",
    "    print('goes in')\n",
    "\n",
    "    up_name = \"tri_media_filtration\" # which unit process it applies to. TODO hould be user input.\n",
    "    cost_range_list = []; #results will be inputted in this array\n",
    "\n",
    "    #for value_change in pct_to_target1: # cycles through each value from MC range\n",
    "    for value_change in list_final:\n",
    "\n",
    "        # create and build model\n",
    "        m = wt.watertap_setup(dynamic = False)\n",
    "        m = wt.case_study_trains.get_case_study(name = 'carlsbad', flow = 4.5833, m = m)\n",
    "\n",
    "        getattr(m.fs, up_name).water_recovery.fix(value_change)\n",
    "\n",
    "        # set variable to MC value\n",
    "        result = wt.run_water_tap(m)\n",
    "        results_table = get_results_table(m, unit_process_names)\n",
    "        cost_range_list.append(results_table.total_up_cost.sum())\n",
    "\n",
    "\n",
    "    return cost_range_list\n",
    "\n",
    "startTime = time.time()\n",
    "\n",
    "pool=Pool()\n",
    "dfs = pool.map(monte_run, list_final) #SomeClass().preprocess_data()\n",
    "\n",
    "executionTime = (time.time() - startTime)\n",
    "print('Execution time in seconds: ' + str(executionTime))"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "####TO DO LOAD AND SAVE!!"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "#### SAVE TRAIN ####\n",
    "# path = 'trains/Tutorial1_treatment_train_example.csv'\n",
    "# wt.save_train(T, path)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# #### LOAD TRAIN ####\n",
    "# path = 'trains/Tutorial1_treatment_train_example.csv'\n",
    "# TT = wt.load_train(path)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# wt.display.show_train(TT)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "celltoolbar": "Raw Cell Format",
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.7.4"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}
