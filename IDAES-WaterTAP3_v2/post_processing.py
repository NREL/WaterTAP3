from pylab import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import write_dot, graphviz_layout
from pyomo.environ import ConcreteModel, SolverFactory, TerminationCondition, \
    value, Var, Constraint, Expression, Objective, TransformationFactory, units as pyunits
from pyomo.network import Arc, SequentialDecomposition
from idaes.core.util.model_statistics import degrees_of_freedom
from pyomo.environ import (
    Block, Constraint, Expression, Var, Param, NonNegativeReals, units as pyunits)
from idaes.core.util.exceptions import ConfigurationError

import case_study_trains
import generate_constituent_list

global scenario
global case_study

up_variables = [
    "fixed_cap_inv",
    "land_cost",
    "working_cap",
    "total_cap_investment",
    "cat_and_chem_cost",
    "electricity_cost",
    "other_var_cost",
    "salaries",
    "benefits",
    "maintenance",
    "lab",
    "insurance_taxes",
    "total_fixed_op_cost",
    "base_employee_salary_cost",
    "electricity"]


def get_results_table(m = None):
    # could make a dictionary if betteR?
    unit_process_names = case_study_trains.get_unit_processes(case_study_trains.case_study)
    
    scenario = case_study_trains.scenario
    case_study = case_study_trains.case_study

    up_name_list = []
    variable_list = []
    value_list = []
    category = []
    unit_list = []

    name_lup = pd.read_csv("data/excel_to_python_names.csv", index_col="Python_variable")

    for b_unit in m.fs.component_objects(Block, descend_into=False):
        if hasattr(b_unit, 'costing'):
            for variable in up_variables:
                up_name_list.append(str(b_unit)[3:])
                variable_list.append(name_lup.loc[variable].Excel_variable)
                value_list.append(value(getattr(b_unit.costing, variable)))
                unit_list.append(name_lup.loc[variable].Unit)
                if variable == "electricity":
                    category.append("Electricity")
                else:
                    category.append("Cost")

            value_list.append(value(getattr(b_unit.costing, "total_up_cost")))
            up_name_list.append(str(b_unit)[3:])
            variable_list.append("Total Unit Cost")
            category.append("Cost")
            unit_list.append("$MM")

            value_list.append((value(getattr(m.fs, str(b_unit)[3:]).flow_vol_in[0])))
            up_name_list.append(str(b_unit)[3:])
            variable_list.append("Inlet Water")
            category.append("Water Flow")
            unit_list.append("m3/s")

            value_list.append((value(getattr(m.fs, str(b_unit)[3:]).flow_vol_out[0])))
            up_name_list.append(str(b_unit)[3:])
            variable_list.append("Outlet Water")
            category.append("Water Flow")
            unit_list.append("m3/s")

            value_list.append(value(getattr(m.fs, str(b_unit)[3:]).flow_vol_waste[0]))
            up_name_list.append(str(b_unit)[3:])
            variable_list.append("Waste Water")
            category.append("Water Flow")
            unit_list.append("m3/s")

            for conc in generate_constituent_list.run():
                ### MASS IN KG PER M3
                value_list.append(value(getattr(m.fs, str(b_unit)[3:]).conc_mass_in[0, conc]))
                up_name_list.append(str(b_unit)[3:])
                variable_list.append("Inlet Constituent")
                category.append(conc)
                unit_list.append("kg/m3")

                value_list.append(value(getattr(m.fs, str(b_unit)[3:]).conc_mass_out[0, conc]))
                up_name_list.append(str(b_unit)[3:])
                variable_list.append("Outlet Constituent")
                category.append(conc)
                unit_list.append("kg/m3")

                value_list.append(value(getattr(m.fs, str(b_unit)[3:]).conc_mass_waste[0, conc]))
                up_name_list.append(str(b_unit)[3:])
                variable_list.append("Waste Constituent")
                category.append(conc)
                unit_list.append("kg/m3")

                ### MASS IN KG --> MULTIPLIED BY FLOW
                value_list.append(value(getattr(m.fs, str(b_unit)[3:]).conc_mass_in[0, conc])*
                                 value(getattr(m.fs, str(b_unit)[3:]).flow_vol_in[0]))
                up_name_list.append(str(b_unit)[3:])
                variable_list.append("Inlet Constituent Total Mass")
                category.append(conc)
                unit_list.append("kg")

                value_list.append(value(getattr(m.fs, str(b_unit)[3:]).conc_mass_out[0, conc])*
                                 value(getattr(m.fs, str(b_unit)[3:]).flow_vol_out[0]))
                up_name_list.append(str(b_unit)[3:])
                variable_list.append("Outlet Constituent Total Mass")
                category.append(conc)
                unit_list.append("kg")

                value_list.append(
                    value(getattr(m.fs, str(b_unit)[3:]).conc_mass_waste[0, conc]) * 
                                value(getattr(m.fs, str(b_unit)[3:]).flow_vol_waste[0]))
                up_name_list.append(str(b_unit)[3:])
                variable_list.append("Waste Constituent Total Mass")
                category.append(conc)
                unit_list.append("kg")            

    for variable in m.fs.costing.component_objects():
        if "CE_index" in str(variable):
            continue
        elif "capital_recovery_factor" in str(variable):
            continue
        else:
            variable_str = str(variable)[11:]
            up_name_list.append("System")
            variable_list.append("System " + name_lup.loc[variable_str].Excel_variable)
            value_list.append(value(getattr(m.fs.costing, variable_str)))
            unit_list.append(name_lup.loc[variable_str].Unit)

            if name_lup.loc[variable_str].Unit == "$MM/yr":
                category.append("Annual Cost")
            else: 
                category.append("Cost")

    df = pd.DataFrame()
    df["Unit Process Name"] = up_name_list
    df["Variable"] = variable_list
    df["Value"] = value_list
    df["Metric"] = category
    df["Unit"] = unit_list
    df["Case Study"] = np.array(case_study)
    df["Scenario"] = np.array(scenario)  
    
    df.Value = df.Value.round(3)
    
    df.to_csv("results/%s_%s_results.csv" % (case_study, scenario))
    
    return df




