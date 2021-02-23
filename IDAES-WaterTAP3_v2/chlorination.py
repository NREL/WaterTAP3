##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2020, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes-pse".
##############################################################################
"""
Demonstration zeroth-order model for WaterTAP3
"""

# Import Pyomo libraries
from pyomo.common.config import ConfigBlock, ConfigValue, In
from pyomo.environ import Block, Constraint, Var, units as pyunits
from pyomo.network import Port

# Import IDAES cores
from idaes.core import (declare_process_block_class,
                        UnitModelBlockData,
                        useDefault)
from idaes.core.util.config import is_physical_parameter_block

from pyomo.environ import (
    Expression, Var, Param, NonNegativeReals, units as pyunits)

# Import WaterTAP# financials module
import financials
from financials import * #ARIEL ADDED

from pyomo.environ import ConcreteModel, SolverFactory, TransformationFactory
from pyomo.network import Arc
from idaes.core import FlowsheetBlock

# Import properties and units from "WaterTAP Library"
from water_props import WaterParameterBlock

from pyomo.network import Arc, SequentialDecomposition
import numpy as np
import pandas as pd

##########################################
####### UNIT PARAMETERS ######
# At this point (outside the unit), we define the unit parameters that do not change across case studies or analyses ######.
# Below (in the unit), we define the parameters that we may want to change across case studies or analyses. Those parameters should be set as variables (eventually) and atttributed to the unit model (i.e. m.fs.UNIT_NAME.PARAMETERNAME). Anything specific to the costing only should be in  m.fs.UNIT_NAME.costing.PARAMETERNAME ######
##########################################

## REFERENCE: Texas Water Board

### MODULE NAME ###
module_name = "chlorination"

# Cost assumptions for the unit, based on the method #
# this is either cost curve or equation. if cost curve then reads in data from file.
unit_cost_method = "cost_curve"
tpec_or_tic = "TPEC"
unit_basis_yr = 2014

#########################################################################
#########################################################################
# TODO: make this part of the model.
contact_time = 1.5  # hours
contact_time_mins = 1.5 * 60
ct = 450  # mg/L-min ---> ASSUME CALI STANDARD FOR NOW
chlorine_decay_rate = 3.0  # mg/Lh

#########################################################################
#########################################################################


# You don't really want to know what this decorator does
# Suffice to say it automates a lot of Pyomo boilerplate for you
@declare_process_block_class("UnitProcess")
class UnitProcessData(UnitModelBlockData):
       
    """
    This class describes the rules for a zeroth-order model for a unit
    """
    # The Config Block is used tpo process arguments from when the model is
    # instantiated. In IDAES, this serves two purposes:
    #     1. Allows us to separate physical properties from unit models
    #     2. Lets us give users options for configuring complex units
    # For WaterTAP3, this will mainly be boilerplate to keep things consistent
    # with ProteusLib and IDAES.
    # The dynamic and has_holdup options are expected arguments which must exist
    # The property package arguments let us define different sets of contaminants
    # without needing to write a new model.
    CONFIG = ConfigBlock()
    CONFIG.declare("dynamic", ConfigValue(
        domain=In([False]),
        default=False,
        description="Dynamic model flag - must be False",
        doc="""Indicates whether this model will be dynamic or not,
**default** = False. Equilibrium Reactors do not support dynamic behavior."""))
    CONFIG.declare("has_holdup", ConfigValue(
        default=False,
        domain=In([False]),
        description="Holdup construction flag - must be False",
        doc="""Indicates whether holdup terms should be constructed or not.
**default** - False. Equilibrium reactors do not have defined volume, thus
this must be False."""))
    CONFIG.declare("property_package", ConfigValue(
        default=useDefault,
        domain=is_physical_parameter_block,
        description="Property package to use for control volume",
        doc="""Property parameter object used to define property calculations,
**default** - useDefault.
**Valid values:** {
**useDefault** - use default package from parent model or flowsheet,
**PhysicalParameterObject** - a PhysicalParameterBlock object.}"""))
    CONFIG.declare("property_package_args", ConfigBlock(
        implicit=True,
        description="Arguments to use for constructing property packages",
        doc="""A ConfigBlock with arguments to be passed to a property block(s)
and used when constructing these,
**default** - None.
**Valid values:** {
see property package for documentation.}"""))
    
    
    from unit_process_equations import initialization
    #unit_process_equations.get_base_unit_process()

    #build(up_name = "chlorination_twb")
    
    def build(self):
        import unit_process_equations
        return unit_process_equations.build_up(self, up_name_test = module_name)
    
    def get_costing(self, module=financials, cost_method="wt", year=None, unit_params = None):
        """
        We need a get_costing method here to provide a point to call the
        costing methods, but we call out to an external consting module
        for the actual calculations. This lets us easily swap in different
        methods if needed.

        Within IDAES, the year argument is used to set the initial value for
        the cost index when we build the model.
        """
        # First, check to see if global costing module is in place
        # Construct it if not present and pass year argument
        if not hasattr(self.flowsheet(), "costing"):
            self.flowsheet().get_costing(module=module, year=year)

        # Next, add a sub-Block to the unit model to hold the cost calculations
        # This is to let us separate costs from model equations when solving
        self.costing = Block()
        # Then call the appropriate costing function out of the costing module
        # The first argument is the Block in which to build the equations
        # Can pass additional arguments as needed
        

        #################################
        #################################

        self.base_fixed_cap_cost = 2.5081
        self.cap_scaling_exp = 0.3238
        self.fixed_op_cost_scaling_exp = 0.7
        
        # basis year for the unit model - based on reference for the method.
        self.costing.basis_year = unit_basis_yr
        
        def get_chlorine_dose_cost(flow_in, dose): # flow in mgd for this cost curve

            import ml_regression
            df = pd.read_csv("data/chlorine_dose_cost_twb.csv") # % dir_path)  # import data
            #df = df[df.Dose != 15] # removing 15 because it would not provide an accurate cost curve - tables assume 10 and 15
            # dose is the same. 15 vs. 10 gives a higher price.

            new_dose_list = np.arange(0, 25.1, 0.5)

            cost_list = []
            flow_list = []
            dose_list = []

            for flow in df.Flow_mgd.unique():
                df_hold = df[df.Flow_mgd == flow]
                del df_hold['Flow_mgd']

                if 0 not in df_hold.Cost.values:
                    xs = np.hstack((0, df_hold.Dose.values)) # dont think we need the 0s
                    ys = np.hstack((0, df_hold.Cost.values)) # dont think we need the 0s
                else:
                    xs = df_hold.Dose.values
                    ys = df_hold.Cost.values

                a = ml_regression.get_cost_curve_coefs(xs = xs, ys = ys)[0][0]
                b = ml_regression.get_cost_curve_coefs(xs = xs, ys = ys)[0][1]

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
            dose_cost_table["flow_mgd"] = flow_list
            dose_cost_table["dose"] = dose_list
            dose_cost_table["cost"] = cost_list
            
            #print("dose:", dose)
            df1 = dose_cost_table[dose_cost_table.dose == dose]
            xs = np.hstack((0, df1.flow_mgd.values)) # dont think we need the 0s
            ys = np.hstack((0, df1.cost.values)) # dont think we need the 0s
            #print(xs)
            #print(df1)
            a = ml_regression.get_cost_curve_coefs(xs = xs, ys = ys)[0][0]
            b = ml_regression.get_cost_curve_coefs(xs = xs, ys = ys)[0][1]

            return (a * flow_in ** b) / 1000 # convert to mil
    
    

        # Get the first time point in the time domain
        # In many cases this will be the only point (steady-state), but lets be
        # safe and use a general approach
        time = self.flowsheet().config.time.first()

        # Get the inlet flow to the unit and convert to the correct units
        flow_in = pyunits.convert(self.flow_vol_in[time],
                                  to_units=pyunits.Mgallons/pyunits.day)

            
        ###### APPLIED CHLORINE DOSE
        self.applied_cl2_dose = chlorine_decay_rate * contact_time + ct / contact_time_mins
                
        ##############################################################################

        # capital costs (unit: MM$) ---> TCI IN EXCEL
        self.costing.fixed_cap_inv_unadjusted = get_chlorine_dose_cost(flow_in, self.applied_cl2_dose) # $M
        
        chem_name = unit_params["chemical_name"][0]
        chem_dict = {chem_name : self.applied_cl2_dose}
        self.chem_dict = chem_dict
                
        self.electricity = .000005689  # kwh/m3 given in PML tab, no source TODO
                
        ##########################################
        ####### GET REST OF UNIT COSTS ######
        ##########################################        
        
        module.get_complete_costing(self.costing)
          
        
# TODO -> BASED ON BLOCKS IN TRAIN!
def get_cl2_dem(m):
    # unit is mg/L. order matters in this list. need a better way.

    seq = SequentialDecomposition()
    G = seq.create_graph(m)
    up_type_list = []
    for node in G.nodes():
        up_type_list.append(str(node).replace('fs.', ''))

    if "secondary_BODonly" in up_type_list:
        return 0
    if "secondary_nitrified" in up_type_list:
        return 5
    if "secondary_denitrified" in up_type_list:
        return 5
    if "mbr" in up_type_list:
        return 4
    if "tertiary_media_filtration" in up_type_list:
        return 5
    if "media_filtration" in up_type_list:
        return 5
    if "biologically_active_filtration" in up_type_list:
        return 2
    if "microfiltration" in up_type_list:

        if "cas" in up_type_list:
            return 12
        elif "nas" in up_type_list:
            return 4
        elif "ozonation" in up_type_list:
            return 3
        elif "o3_baf" in up_type_list:
            return 2
        else:
            return 0
    if "ultrafiltration" in up_type_list:

        if "cas" in up_type_list:
            return 12
        elif "nas" in up_type_list:
            return 4
        elif "ozonation" in up_type_list:
            return 3
        elif "o3_baf" in up_type_list:
            return 2
        else:
            return 0
    if "ozonation" in up_type_list:
        return 3
    if "uv" in up_type_list:
        return 0
    if "reverse_osomisis" in up_type_list:
        return 0

    print("assuming initial chlorine demand is 0")

    return 0    
        
        
def get_additional_variables(self, units_meta, time):
    
    self.cl2_dem = Var(time, initialize=0, units=pyunits.dimensionless, doc="initial chlorine demand")    
    
  


