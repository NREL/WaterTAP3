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
    "m = wt.case_study_trains.get_case_study(m = m)"
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
   "execution_count": 7,
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
       "<IPython.lib.display.IFrame at 0x7fb8ffd0ff50>"
      ]
     },
     "execution_count": 7,
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
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": 8,
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
      "Number of nonzeros in equality constraint Jacobian...:      717\n",
      "Number of nonzeros in inequality constraint Jacobian.:        0\n",
      "Number of nonzeros in Lagrangian Hessian.............:      180\n",
      "\n",
      "Total number of variables............................:      240\n",
      "                     variables with only lower bounds:       15\n",
      "                variables with lower and upper bounds:      135\n",
      "                     variables with only upper bounds:        0\n",
      "Total number of equality constraints.................:      240\n",
      "Total number of inequality constraints...............:        0\n",
      "        inequality constraints with only lower bounds:        0\n",
      "   inequality constraints with lower and upper bounds:        0\n",
      "        inequality constraints with only upper bounds:        0\n",
      "\n",
      "iter    objective    inf_pr   inf_du lg(mu)  ||d||  lg(rg) alpha_du alpha_pr  ls\n",
      "   0  0.0000000e+00 1.60e+05 1.00e+00  -1.0 0.00e+00    -  0.00e+00 0.00e+00   0\n",
      "   1  0.0000000e+00 5.62e+05 2.83e+13  -1.0 1.60e+05    -  6.17e-08 9.90e-01f  1\n",
      "   2  0.0000000e+00 1.23e+03 2.22e+13  -1.0 1.25e+05    -  9.90e-01 9.90e-01h  1\n",
      "   3  0.0000000e+00 1.21e+01 2.20e+11  -1.0 2.72e+02    -  9.90e-01 9.90e-01h  1\n",
      "   4  0.0000000e+00 8.35e-06 3.09e+04  -1.0 2.67e+00    -  9.90e-01 1.00e+00h  1\n",
      "   5  0.0000000e+00 9.90e-07 8.95e+01  -1.0 9.90e-07   8.0 9.90e-01 1.00e+00f  1\n",
      "   6  0.0000000e+00 2.91e-11 1.52e+02  -1.7 1.83e-06    -  9.92e-01 1.00e+00h  1\n",
      "Cannot recompute multipliers for feasibility problem.  Error in eq_mult_calculator\n",
      "\n",
      "Number of Iterations....: 6\n",
      "\n",
      "                                   (scaled)                 (unscaled)\n",
      "Objective...............:   0.0000000000000000e+00    0.0000000000000000e+00\n",
      "Dual infeasibility......:   1.2032550877845124e+05    1.2032550877845124e+05\n",
      "Constraint violation....:   2.9103830456852301e-11    2.9103830456852301e-11\n",
      "Complementarity.........:   0.0000000000000000e+00    0.0000000000000000e+00\n",
      "Overall NLP error.......:   2.9103830456852301e-11    1.2032550877845124e+05\n",
      "\n",
      "\n",
      "Number of objective function evaluations             = 7\n",
      "Number of objective gradient evaluations             = 7\n",
      "Number of equality constraint evaluations            = 7\n",
      "Number of inequality constraint evaluations          = 0\n",
      "Number of equality constraint Jacobian evaluations   = 7\n",
      "Number of inequality constraint Jacobian evaluations = 0\n",
      "Number of Lagrangian Hessian evaluations             = 6\n",
      "Total CPU secs in IPOPT (w/o function evaluations)   =      0.066\n",
      "Total CPU secs in NLP function evaluations           =      0.001\n",
      "\n",
      "EXIT: Optimal Solution Found.\n",
      "\b----------------------------------------------------------------------\n",
      "fs.sw_onshore_intake\n",
      "inlet : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 66.3, (0.0, 'calcium'): 409.6, (0.0, 'chloride'): 19162.0, (0.0, 'magnesium'): 1278.0, (0.0, 'potassium'): 395.3, (0.0, 'sodium'): 10679.0, (0.0, 'strontium'): 1.3, (0.0, 'sulfate'): 2680.0, (0.0, 'tds'): 34999.99999999999}\n",
      "         :    flow_vol : {0.0: 4.5833}\n",
      "         :    pressure : {0.0: 199999.9999}\n",
      "         : temperature : {0.0: 300.0}\n",
      "outlet : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 66.3, (0.0, 'calcium'): 409.6000000000001, (0.0, 'chloride'): 19162.0, (0.0, 'magnesium'): 1278.0, (0.0, 'potassium'): 395.3, (0.0, 'sodium'): 10679.0, (0.0, 'strontium'): 1.3, (0.0, 'sulfate'): 2680.0, (0.0, 'tds'): 34999.99999999999}\n",
      "         :    flow_vol : {0.0: 4.5833}\n",
      "         :    pressure : {0.0: 199999.9998}\n",
      "         : temperature : {0.0: 300.0}\n",
      "waste : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 0.010000989950588667, (0.0, 'calcium'): 0.010000989950588672, (0.0, 'chloride'): 0.010000989950588691, (0.0, 'magnesium'): 0.01000098995058868, (0.0, 'potassium'): 0.01000098995058869, (0.0, 'sodium'): 0.010000989950588702, (0.0, 'strontium'): 0.010000989950588695, (0.0, 'sulfate'): 0.010000989950588688, (0.0, 'tds'): 0.010000989950588698}\n",
      "         :    flow_vol : {0.0: 0.0}\n",
      "         :    pressure : {0.0: 199999.9998}\n",
      "         : temperature : {0.0: 300.0}\n",
      "total_cap_investment: 22.06079141440889\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "fs.sulfuric_acid_addition\n",
      "inlet : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 66.3, (0.0, 'calcium'): 409.6000000000001, (0.0, 'chloride'): 19162.0, (0.0, 'magnesium'): 1278.0, (0.0, 'potassium'): 395.3, (0.0, 'sodium'): 10679.0, (0.0, 'strontium'): 1.3, (0.0, 'sulfate'): 2680.0, (0.0, 'tds'): 34999.99999999999}\n",
      "         :    flow_vol : {0.0: 4.5833}\n",
      "         :    pressure : {0.0: 199999.9998}\n",
      "         : temperature : {0.0: 300.0}\n",
      "outlet : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 66.3, (0.0, 'calcium'): 409.6000000000001, (0.0, 'chloride'): 19162.0, (0.0, 'magnesium'): 1278.0, (0.0, 'potassium'): 395.3, (0.0, 'sodium'): 10678.999999999998, (0.0, 'strontium'): 1.3, (0.0, 'sulfate'): 2680.0, (0.0, 'tds'): 34999.99999999999}\n",
      "         :    flow_vol : {0.0: 4.5833}\n",
      "         :    pressure : {0.0: 199999.9997}\n",
      "         : temperature : {0.0: 300.0}\n",
      "waste : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 0.010000969215248932, (0.0, 'calcium'): 0.01000096921524894, (0.0, 'chloride'): 0.010000969215248935, (0.0, 'magnesium'): 0.010000969215248937, (0.0, 'potassium'): 0.010000969215248939, (0.0, 'sodium'): 0.010000969215248947, (0.0, 'strontium'): 0.010000969215248956, (0.0, 'sulfate'): 0.010000969215249001, (0.0, 'tds'): 0.010000969215248989}\n",
      "         :    flow_vol : {0.0: 5.929230630780102e-21}\n",
      "         :    pressure : {0.0: 199999.9997}\n",
      "         : temperature : {0.0: 300.0}\n",
      "total_cap_investment: 0.014066538929476105\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "fs.treated_storage\n",
      "inlet : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 66.3, (0.0, 'calcium'): 409.6000000000001, (0.0, 'chloride'): 19162.0, (0.0, 'magnesium'): 1278.0, (0.0, 'potassium'): 395.3, (0.0, 'sodium'): 10678.999999999998, (0.0, 'strontium'): 1.3, (0.0, 'sulfate'): 2680.0, (0.0, 'tds'): 34999.99999999999}\n",
      "         :    flow_vol : {0.0: 4.5833}\n",
      "         :    pressure : {0.0: 199999.9997}\n",
      "         : temperature : {0.0: 300.0}\n",
      "outlet : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 66.3, (0.0, 'calcium'): 409.6000000000001, (0.0, 'chloride'): 19162.0, (0.0, 'magnesium'): 1278.0, (0.0, 'potassium'): 395.3, (0.0, 'sodium'): 10678.999999999998, (0.0, 'strontium'): 1.2999999999999499, (0.0, 'sulfate'): 2680.0000000000005, (0.0, 'tds'): 35000.0}\n",
      "         :    flow_vol : {0.0: 4.5833}\n",
      "         :    pressure : {0.0: 199999.99959999998}\n",
      "         : temperature : {0.0: 300.0}\n",
      "waste : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 0.01000096921524919, (0.0, 'calcium'): 0.010000969215249185, (0.0, 'chloride'): 0.010000969215249206, (0.0, 'magnesium'): 0.010000969215249199, (0.0, 'potassium'): 0.010000969215249183, (0.0, 'sodium'): 0.010000969215249206, (0.0, 'strontium'): 0.010000969215249199, (0.0, 'sulfate'): 0.010000969215249202, (0.0, 'tds'): 0.010000969215249194}\n",
      "         :    flow_vol : {0.0: 1.1858461261560205e-20}\n",
      "         :    pressure : {0.0: 199999.99959999998}\n",
      "         : temperature : {0.0: 300.0}\n",
      "total_cap_investment: 18.964032428480344\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "fs.surface_discharge\n",
      "inlet : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 0.02000200745743435, (0.0, 'calcium'): 0.02000200745743456, (0.0, 'chloride'): 0.020002007457434395, (0.0, 'magnesium'): 0.020002007457434502, (0.0, 'potassium'): 0.020002007457434565, (0.0, 'sodium'): 0.020002007457434568, (0.0, 'strontium'): 0.020002007457434686, (0.0, 'sulfate'): 0.020002007457434724, (0.0, 'tds'): 0.020002007457435005}\n",
      "         :    flow_vol : {0.0: 1.7787691892340307e-20}\n",
      "         :    pressure : {0.0: 199999.99955}\n",
      "         : temperature : {0.0: 299.9999}\n",
      "outlet : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 0.0200019979104234, (0.0, 'calcium'): 0.020001997910423605, (0.0, 'chloride'): 0.020001997910423442, (0.0, 'magnesium'): 0.02000199791042355, (0.0, 'potassium'): 0.02000199791042362, (0.0, 'sodium'): 0.020001997910423615, (0.0, 'strontium'): 0.020001997910423733, (0.0, 'sulfate'): 0.020001997910423785, (0.0, 'tds'): 0.020001997910424067}\n",
      "         :    flow_vol : {0.0: 1.7787691892340307e-20}\n",
      "         :    pressure : {0.0: 199999.99945}\n",
      "         : temperature : {0.0: 299.9999}\n",
      "waste : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 0.010000989013741066, (0.0, 'calcium'): 0.010000989013741067, (0.0, 'chloride'): 0.010000989013741066, (0.0, 'magnesium'): 0.010000989013741069, (0.0, 'potassium'): 0.010000989013741066, (0.0, 'sodium'): 0.010000989013741067, (0.0, 'strontium'): 0.010000989013741064, (0.0, 'sulfate'): 0.010000989013741064, (0.0, 'tds'): 0.010000989013741069}\n",
      "         :    flow_vol : {0.0: 0.0}\n",
      "         :    pressure : {0.0: 199999.99945}\n",
      "         : temperature : {0.0: 299.9999}\n",
      "total_cap_investment: 8.329624263650956e-17\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "fs.municipal_drinking\n",
      "inlet : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 66.3, (0.0, 'calcium'): 409.6000000000001, (0.0, 'chloride'): 19162.0, (0.0, 'magnesium'): 1278.0, (0.0, 'potassium'): 395.3, (0.0, 'sodium'): 10678.999999999998, (0.0, 'strontium'): 1.2999999999999499, (0.0, 'sulfate'): 2680.0000000000005, (0.0, 'tds'): 35000.0}\n",
      "         :    flow_vol : {0.0: 4.583300000000348}\n",
      "         :    pressure : {0.0: 199999.99959999998}\n",
      "         : temperature : {0.0: 300.0}\n",
      "outlet : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 66.29999999999937, (0.0, 'calcium'): 409.59999999999627, (0.0, 'chloride'): 19161.999999999818, (0.0, 'magnesium'): 1277.9999999999877, (0.0, 'potassium'): 395.29999999999626, (0.0, 'sodium'): 10678.999999999898, (0.0, 'strontium'): 1.2999999999999376, (0.0, 'sulfate'): 2679.9999999999745, (0.0, 'tds'): 34999.999999999665}\n",
      "         :    flow_vol : {0.0: 4.58330000000039}\n",
      "         :    pressure : {0.0: 199999.9995}\n",
      "         : temperature : {0.0: 300.0}\n",
      "waste : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 0.010000986552649561, (0.0, 'calcium'): 0.010000986552649561, (0.0, 'chloride'): 0.010000986552649558, (0.0, 'magnesium'): 0.010000986552649565, (0.0, 'potassium'): 0.01000098655264956, (0.0, 'sodium'): 0.010000986552649565, (0.0, 'strontium'): 0.010000986552649558, (0.0, 'sulfate'): 0.01000098655264956, (0.0, 'tds'): 0.010000986552649563}\n",
      "         :    flow_vol : {0.0: 2.434938703235203e-13}\n",
      "         :    pressure : {0.0: 199999.9995}\n",
      "         : temperature : {0.0: 300.0}\n",
      "total_cap_investment: 8.071285171652809\n",
      "----------------------------------------------------------------------\n",
      "----------------------------------------------------------------------\n",
      "fs.Seawater\n",
      "inlet : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 66.3, (0.0, 'calcium'): 409.6, (0.0, 'chloride'): 19162.0, (0.0, 'magnesium'): 1278.0, (0.0, 'potassium'): 395.3, (0.0, 'sodium'): 10679.0, (0.0, 'strontium'): 1.3, (0.0, 'sulfate'): 2680.0, (0.0, 'tds'): 35000.0}\n",
      "         :    flow_vol : {0.0: 4.5833}\n",
      "         :    pressure : {0.0: 200000.0}\n",
      "         : temperature : {0.0: 300}\n",
      "outlet : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 66.3, (0.0, 'calcium'): 409.6, (0.0, 'chloride'): 19162.0, (0.0, 'magnesium'): 1278.0, (0.0, 'potassium'): 395.3, (0.0, 'sodium'): 10679.0, (0.0, 'strontium'): 1.3, (0.0, 'sulfate'): 2680.0, (0.0, 'tds'): 34999.99999999999}\n",
      "         :    flow_vol : {0.0: 4.5833}\n",
      "         :    pressure : {0.0: 199999.9999}\n",
      "         : temperature : {0.0: 300.0}\n",
      "waste : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): -3.520738470652223e-19, (0.0, 'calcium'): -5.205897635975254e-23, (0.0, 'chloride'): -3.3000868836907415e-22, (0.0, 'magnesium'): -6.49571941229483e-23, (0.0, 'potassium'): -5.183616022022639e-23, (0.0, 'sodium'): -2.0367491121274949e-22, (0.0, 'strontium'): -4.601311475663205e-23, (0.0, 'sulfate'): -8.576538016801377e-23, (0.0, 'tds'): -5.6384060966749815e-22}\n",
      "         :    flow_vol : {0.0: -1.5597557851304593e-16}\n",
      "         :    pressure : {0.0: 199999.9999}\n",
      "         : temperature : {0.0: 300.0}\n",
      "outlet : Size=1\n",
      "    Key  : Name        : Value\n",
      "    None :   conc_mass : {(0.0, 'bromide'): 0.02000200745743435, (0.0, 'calcium'): 0.02000200745743456, (0.0, 'chloride'): 0.020002007457434395, (0.0, 'magnesium'): 0.020002007457434502, (0.0, 'potassium'): 0.020002007457434565, (0.0, 'sodium'): 0.020002007457434568, (0.0, 'strontium'): 0.020002007457434686, (0.0, 'sulfate'): 0.020002007457434724, (0.0, 'tds'): 0.020002007457435005}\n",
      "         :    flow_vol : {0.0: 1.7787691892340307e-20}\n",
      "         :    pressure : {0.0: 199999.99955}\n",
      "         : temperature : {0.0: 299.9999}\n"
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
