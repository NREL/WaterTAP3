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

import numpy as np
import pandas as pd
# Import IDAES cores
from idaes.core import (UnitModelBlockData, declare_process_block_class, useDefault)
from idaes.core.util.config import is_physical_parameter_block
# Import Pyomo libraries
from pyomo.common.config import ConfigBlock, ConfigValue, In
from scipy.optimize import curve_fit
from cost_curves import cost_curve
# Import WaterTAP# financials module
import financials
from financials import *  # ARIEL ADDED
from pyomo.environ import NonNegativeReals
from pyomo.environ import *

# Import properties and units from "WaterTAP Library"

##########################################
####### UNIT PARAMETERS ######
# At this point (outside the unit), we define the unit parameters that do not change across case studies or analyses ######.
# Below (in the unit), we define the parameters that we may want to change across case studies or analyses. Those parameters should be set as variables (eventually) and atttributed to the unit model (i.e. m.fs.UNIT_NAME.PARAMETERNAME). Anything specific to the costing only should be in  m.fs.UNIT_NAME.costing.PARAMETERNAME ######
##########################################

## REFERENCE: Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura)

### MODULE NAME ###
module_name = "anion_exchange_epa"

# Cost assumptions for the unit, based on the method #
# this is either cost curve or equation. if cost curve then reads in data from file.
unit_cost_method = "cost_curve"
tpec_or_tic = "TPEC"
unit_basis_yr = 2012


# You don't really want to know what this decorator does
# Suffice to say it automates a lot of Pyomo boilerplate for you
@declare_process_block_class("UnitProcess")
class UnitProcessData(UnitModelBlockData):
    """
    This class describes the rules for a zeroth-order model for a unit

    The Config Block is used tpo process arguments from when the model is
    instantiated. In IDAES, this serves two purposes:
         1. Allows us to separate physical properties from unit models
         2. Lets us give users options for configuring complex units
    The dynamic and has_holdup options are expected arguments which must exist
    The property package arguments let us define different sets of contaminants
    without needing to write a new model.
    """

    CONFIG = ConfigBlock()
    CONFIG.declare("dynamic", ConfigValue(domain=In([False]), default=False, description="Dynamic model flag - must be False", doc="""Indicates whether this model will be dynamic or not,
**default** = False. Equilibrium Reactors do not support dynamic behavior."""))
    CONFIG.declare("has_holdup", ConfigValue(default=False, domain=In([False]), description="Holdup construction flag - must be False", doc="""Indicates whether holdup terms should be constructed or not.
**default** - False. Equilibrium reactors do not have defined volume, thus
this must be False."""))
    CONFIG.declare("property_package", ConfigValue(default=useDefault, domain=is_physical_parameter_block, description="Property package to use for control volume", doc="""Property parameter object used to define property calculations,
**default** - useDefault.
**Valid values:** {
**useDefault** - use default package from parent model or flowsheet,
**PhysicalParameterObject** - a PhysicalParameterBlock object.}"""))
    CONFIG.declare("property_package_args", ConfigBlock(implicit=True, description="Arguments to use for constructing property packages", doc="""A ConfigBlock with arguments to be passed to a property block(s)
and used when constructing these,
**default** - None.
**Valid values:** {
see property package for documentation.}"""))

    def build(self):
        import unit_process_equations
        return unit_process_equations.build_up(self, up_name_test=module_name)

    # NOTE ---> THIS SHOULD EVENTUaLLY BE JUST FOR COSTING INFO/EQUATIONS/FUNCTIONS. EVERYTHING ELSE IN ABOVE.
    def get_costing(self, module=financials, cost_method="wt", year=None, unit_params=None):
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
        global res_stagger_time, num_treat_lines, water_flush, basin_op_depth, tss_residuals, res_flow_annual, transport_min, disposal_miles, transport_unit, disposal, max_sa, media_volume, comm_sa, void_above
        if not hasattr(self.flowsheet(), "costing"):
            self.flowsheet().get_costing(module=module, year=year)

        # Next, add a sub-Block to the unit model to hold the cost calculations
        # This is to let us separate costs from model equations when solving
        self.costing = Block()
        # Then call the appropriate costing function out of the costing module
        # The first argument is the Block in which to build the equations
        # Can pass additional arguments as needed

        ##########################################
        ####### UNIT SPECIFIC VARIABLES AND CONSTANTS -> SET AS SELF OTHERWISE LEAVE AT TOP OF FILE ######
        ##########################################

        time = self.flowsheet().config.time
        t = self.flowsheet().config.time.first()
        # get tic or tpec (could still be made more efficent code-wise, but could enough for now)
        sys_cost_params = self.parent_block().costing_param
        self.costing.tpec_tic = sys_cost_params.tpec if tpec_or_tic == "TPEC" else sys_cost_params.tic
        tpec_tic = self.costing.tpec_tic
        # basis year for the unit model - based on reference for the method.
        self.costing.basis_year = unit_basis_yr
        # system_type = unit_params
        # ebct_init = Block()
        self.ebct = Var(time, initialize=5, domain=NonNegativeReals, bounds=(0.1, 100), units=pyunits.minutes, doc="ebct")
        self.ebct.fix(unit_params['ebct'])

        flow_in = pyunits.convert(self.flow_vol_in[t], to_units=pyunits.Mgallons / pyunits.day)
        # self.ebct = unit_params['ebct']
        try:
            self.freund1 = unit_params['freund1']  # Kf (ug/g)(L/ug)1/n
            self.freund2 = unit_params['freund2']  # dimensionless
            self.conc_in = unit_params['conc_in']
            self.conc_breakthru = unit_params['conc_breakthru']
            self.ph_in = unit_params['ph_in']
            self.ph_out = unit_params['ph_out']
        except:
            # defaults to values for nitrate removal using polystyrenic gel-type resin and 99% reduction (1 mg/L --> 0.01 mg/L)
            self.freund1 = 21.87
            self.freund2 = 3.04
            self.conc_in = 10
            self.conc_breakthru = 0.1
            self.ph_in = 7
            self.ph_out = 8.2

        try:
            geom = unit_params['geom']
            pv_material = unit_params['pv_material']
            bw_tank_type = unit_params['bw_tank_type']
            self.resin_name = unit_params['resin_type']
        except:
            geom = 'vertical'
            pv_material = 'stainless'
            bw_tank_type = 'stainless'
            self.resin_name = 'styrenic_gel_1'
        
                
        resin_type_list = ['styrenic_gel_1', 'styrenic_gel_2', 'styrenic_macro_1', 'styrenic_macro_2', 'polyacrylic', 'nitrate', 'custom']
        
        self.resin_dict = {'styrenic_gel_1' : 148, 
                      'styrenic_gel_2' : 173, 
                      'styrenic_macro_1' : 207, 
                      'styrenic_macro_2' : 221, 
                      'polyacrylic' : 245, 
                      'nitrate': 173}

        self.anion_res_capacity = Var(time, initialize=10, domain=NonNegativeReals, 
                                      doc="anion exchange resin capacity")  # anion exchange capacity -- kgr/ft3

        self.cation_res_capacity = Var(time, 
                                       initialize=10, domain=NonNegativeReals,
                                       doc="cation exchange resin capacity")  # cation exchange capacity -- kgr/ft3

        # self.mass_removed = self.mass_tds_in * self.removal_fraction * 1000  # mass to be removed in kgr/ft3
        self.mass_removed = Var(time, initialize=70, domain=NonNegativeReals, doc="mass removed")

        self.rinse_volume = Var(time, initialize=70, domain=NonNegativeReals, doc="rinse volume for anion exchange resin") # gal/ft3 resin
        
        self.anion_resin_volume = Var(time, initialize=10, domain=NonNegativeReals, doc="anion exchange resin volume") # ft3
        self.cation_resin_volume = Var(time, initialize=10, domain=NonNegativeReals, doc="cation exchange resin volume") # ft3

        self.anion_rinse_flow = Var(time, initialize=10, domain=NonNegativeReals, doc="anion exchange rinse flow") #gal/day

        self.anion_rinse_solids = Var(time, initialize=10, domain=NonNegativeReals, doc="additional cations from anion rinse volume")
        self.an_vol_per_unit = Var(time, initialize=10, domain=NonNegativeReals, doc="additional cations from anion rinse volume") # anion exchange resin per unit
        self.cat_vol_per_unit = Var(time, initialize=10, domain=NonNegativeReals, doc="additional cations from anion rinse volume") # cation exchange resin per unit
        
        flow_waste_gal_day = pyunits.convert(self.flow_vol_waste[t], to_units=pyunits.gallons / pyunits.day)
        flow_in_gal_day = pyunits.convert(self.flow_vol_in[t], to_units=pyunits.gallons / pyunits.day)
        flow_out_gal_day = pyunits.convert(self.flow_vol_out[t], to_units=pyunits.gallons / pyunits.day)
                
        self.num_ix_units_op = Var(time, initialize=3, domain=NonNegativeReals, doc="number of IX operating units") ## NEEDS TO BE IN INTEGERS operational units
        self.num_ix_units_tot = Var(time, initialize=3, domain=NonNegativeReals, 
                                    doc="number of IX total units") ## NEEDS TO BE IN INTEGERS total units (op - 1)
        self.loading_rate = Var(time, initialize=5, doc='loading rate') # gpm/ft2
        self.an_load_per_unit = Var(time, initialize=5, doc='an loading rate')
        self.cat_load_per_unit = Var(time, initialize=5, doc='cat loading rate')

        self.an_tank_diam = Var(time, initialize=5, bounds=(4,14), doc='an tank diam')
        self.an_tank_depth = Var(time, initialize=5, bounds=(3,9), doc='tank depth')

        self.cat_tank_diam = Var(time, initialize=5, bounds=(4,14), doc='cat tank diam')
        self.cat_tank_depth = Var(time, initialize=5, bounds=(3,9), doc='tank depth')
        
        self.anion_res_capacity.fix(16)
        self.cation_res_capacity.fix(18)
        self.rinse_volume.fix(70)
        self.num_ix_units_op.unfix()
        self.loading_rate.fix(5)
        
        self.water_recovery_constraint = Constraint(
            expr = self.water_recovery[t] * flow_in_gal_day == flow_out_gal_day
        )
       
       
        self.mass_removed_constr = Constraint(
            expr=self.mass_removed[t] * 1000 == (500 / 17.12) * flow_out_gal_day
        ) # mass removed kgr/day
        
        self.an_res_vol_constr = Constraint(
            expr=self.anion_resin_volume[t] * self.anion_res_capacity[t] == self.mass_removed[t]) # ft3/day

        self.cation_res_vol_constr = Constraint(
            expr=self.cation_resin_volume[t] * self.cation_res_capacity[t] == self.mass_removed[t] + self.anion_rinse_solids[t]) # ft3/day        
        
        self.an_rins_vol_constr = Constraint(
            expr=flow_waste_gal_day == self.anion_resin_volume[t] * self.rinse_volume[t]) # gal/day    
        
        self.an_rinse_solids_constr = Constraint(
            expr=self.anion_rinse_solids[t] == flow_waste_gal_day * (self.mass_removed[t] / 100) /1000)# Kgr/day  


        self.an_vol_per_unit_constr = Constraint(
            expr=self.an_vol_per_unit[t] == self.anion_resin_volume[t] / self.num_ix_units_op[t])
        
        self.cat_vol_per_unit_constr = Constraint(
            expr=self.cat_vol_per_unit[t] == self.cation_resin_volume[t] / self.num_ix_units_op[t])


        self.an_tank_depth_constr = Constraint(
        expr = self.an_tank_depth[t] == self.an_vol_per_unit[t] / 
        ((((flow_in_gal_day / (self.num_ix_units_op[t] - 1)) / 1440) / self.loading_rate[t]) * 1.22)
        )
        
        self.cat_tank_depth_constr = Constraint(
        expr = self.cat_tank_depth[t] == self.cat_vol_per_unit[t] / 
        ((((flow_in_gal_day / (self.num_ix_units_op[t] - 1)) / 1440) / self.loading_rate[t]) * 1.22)
        )
        
        
        
#         self.cat_tank_diam_constr = Constraint(
#             expr=self.an_vol_per_unit[t] == self.anion_resin_volume[t] / self.num_ix_units_op[t]
#         )
        
#         self.cat_vol_per_unit_constr = Constraint(
#             expr=self.cat_vol_per_unit[t] == self.cation_resin_volume[t] / self.num_ix_units_op[t]
#         )       
        
        
        
        
        
#         self.an_res_vol_constr = Constraint(expr=self.anion_resin_volume[t] * self.anion_res_capacity[t] == self.mass_removed[t]) # ft3/day
#         self.cat_res_vol_constr = Constraint(expr=self.cation_resin_volume[t] * self.cation_res_capacity[t] == self.mass_removed[t] + self.anion_rinse_solids[t]) # ft3/day
#         self.an_rins_vol_constr = Constraint(expr=self.anion_rinse_flow[t] == self.anion_resin_volume[t] * self.rinse_volume[t]) # gal/day
#         self.an_rinse_solids_constr = Constraint(expr=self.anion_rinse_solids[t] == self.anion_rinse_flow[t] * self.mass_removed[t]) # Kgr/day
#         self.num_units_constr = Constraint(expr=self.num_ix_units_op[t] == self.num_ix_units_tot[t] - 1) # number operating units is one less than total units -- assume one is offline at all times for
#         # regeneration
#         self.an_vol_per_unit_constr = Constraint(expr=self.an_vol_per_unit[t] == self.anion_resin_volume[t] / self.num_ix_units_op[t])
# #         self.cat_vol_per_unit_constr = Constraint(expr=self.cat_vol_per_unit[t] == self.cation_resin_volume[t] / self.num_ix_units_op[t])

#         self.an_loading_constr = Constraint(expr=self.an_load_per_unit[t]  == (self.an_vol_per_unit[t] / 1440) / self.loading_rate[t])
#         self.cat_loading_constr = Constraint(expr=self.cat_load_per_unit[t] == (self.cat_vol_per_unit[t] / 1440) / self.loading_rate[t])

#         self.an_tank_diam_constr = Constraint(expr=2 * ((self.an_load_per_unit[t] * 1.5) / 3.14159) ** 0.5 == self.an_tank_diam[t])
#         self.an_tank_depth_constr = Constraint(expr=self.an_vol_per_unit[t] / (self.an_load_per_unit[t] * 1.5) == self.an_tank_depth[t])

#         self.cat_tank_diam_constr = Constraint(expr=2 * ((self.cat_load_per_unit[t] * 1.5) / 3.14159) ** 0.5 == self.cat_tank_diam[t])
#         self.cat_tank_depth_constr = Constraint(expr=self.cat_vol_per_unit[t] / (self.cat_load_per_unit[t] * 1.5) == self.cat_tank_depth[t])
        
        
        

        #self.resin_cost = Var(time, initialize=100, domain=NonNegativeReals, bounds=(0, 500), doc="lookupvalue")
        
        #self._anresin_cost.fix(self.resin_dict[self.resin_name])
                #cat
        
        ############## SYSTEM INPUTS ##############

        ########################################################
        ########################################################
        ############## CRITICAL DESIGN ASSUMPTIONS ##############
        ########################################################
        ########################################################

#         ############## VESSEL DESIGN ##############
#         comm_diam = 5.5  # * pyunits.ft # vessel diameter ??
#         bed_depth = 4.3  # * pyunits.ft # vessel bed depth
#         chem_store = 30  # * pyunits.days # days of chemical storage
#         salt_purchase = 33733  # * pyunits.lbs # amount of NaCl needed for purchase; depends on size of purchase
#         comm_height_length = 7  # * pyunits.ft # "straight" height of vessel ??
#         num_redund_small_1 = 1  # Number of redundant vessels for small systems with only one vessel -- If a design includes only one operating vessel, there should be at least one additional vessel
#         num_redund_small = 0  # Number of redundant vessels for small systems with multiple vessels -- Small systems can operate at reduced capacity while one vessel is down for backwash, if there are multiple vessels
#         redund_freq = 4  # Add a redundant unit per x parallel lines
#         bp_pct = 0.15  # * pyunits.dimensionless # bypass percent of flow -- Typically, bypass flow ranges between 0% and 50% of inflow. Enter zero to remove bypass piping and components. 0% is default consistent with the type of cost curves that EPA will need for its national cost simulation model.
#         load_min = 4  # * (pyunits.gallons / pyunits.minute / pyunits.feet ** 2) # Loading rate minimum -- Based on peer review
#         load_max = 16  # * (pyunits.gallons / pyunits.minute / pyunits.feet ** 2) # Loading rate maximum -- Based on peer review
#         max_height = 14  # * pyunits.ft # Maximum vessel height (circular vessels) -- Systems have used vessels up to 14' diam and height in practice (AWWA Inorganic Contaminants Workshop 2006)
#         # max_diam_override =
#         max_length = 53  # * pyunits.ft #Maximum vessel length (longitudinal vessels) -- Maximum vessel diameter will be chosen from a table of conventional sizes for commercial vessels, unless entered here.  Systems have used vessels up to 14' diam and height in practice (AWWA Inorganic Contaminants Workshop 2006)
#         freeboard = 0.5  # * pyunits.ft # free board above media at full expansion --
#         horiz_underdrain = 1.5  # * pyunits.ft # underdrain space for horizontal vessels -- 1.5 feet is a conservative value for a 10' tank. Bob Dvorin, 5/16/05.
#         vessel_thickness = 0  # * pyunits.ft # thickness of vessel walls ? -- Set to zero because vendor designs and quotes are usually expressed in inside diameter.  Increase if user desires to input outside diameter.
#         length_diam_ratio = 2.5  # -- Used only for autosize procedure
#         bed_expansion = 0.5  # * pyunits.dimensionless # resin expansion during backwash -- Boodoo peer review comments
#         media_density = 43  # * (pyunits.lbs / pyunits.ft ** 3) # varies between 41-46 lbs/ft3 --
#         min_bed_depth = 2.5  # * pyunits.ft # minimum bed depth for autosize -- Guidance: Typically bypass flow ranges between 10 % and 50 % of inflow.  Enter zero to remove bypass piping and components. 0%
#         # is default consistent with the type of cost curves that EPA will need for its national cost simulation model
#         max_bed_depth = 6
#         target_bed_depth_under = 3.2  # * pyunits.ft # Target Bed Depth (Designs < 1MGD) -- used for autosize
#         target_bed_depth_over = 4.6  # * pyunits.ft # Target Bed Depth (Vertical Designs > 1 MGD) -- used for autosize
#         target_bed_depth_horiz = 4.3  # * pyunits.ft # Target Bed Depth (Horizontal Designs) -- used for autosize
#         vol_tol_vert_small = 0.5  # Volume Tolerance, vertical vessels <1 mgd -- Used to check size compatibility of specified volume with required volume
#         vol_tol_vert_med = 0.4  # Volume Tolerance, vertical vessels >1 mgd
#         vol_tol_horiz = 0.4  # Volume Tolerance, horizontal vessels

#         ############## PUMPING ##############

#         pump_safety_factor = 0.25
#         num_redund_pumps = 0
#         num_redund_back_pumps = 1
#         num_redund_pH_pumps = 1
#         num_redund_cm_pump = 1
#         min_avg_flow = 0.1  # Minimum average flow as percentage of design

#         ############## BACKWASH AND REGENERATION ##############
#         backwash_load_rate = 3  # * (pyunits.gallon / pyunits.minute) / pyunits.ft**2 # backwash loading rate -- 1-5 gpm/square ft
#         backwash_time = 12  # * pyunits.minutes # backwashing time -- 10 to 15 minutes.  12 minutes gives 1 BV of water at 2 gpm/square ft (Lowry Peer Review comments)
#         # add_backwash_freq = # -- Leave blank to assume backwash occurs only at regneration, enter a value to incorporate additional, out-of-cycle backwashes
#         salt_dose = 8  # * (pyunits.lb / pyunits.ft ** 3) # salt dose for resin regen -- 8 lbs/cubic foot is more than adequate to remove divalent anions (Boodo Peer Review comments)
#         regen_rate = 0.8  # * (pyunits.gallon / pyunits.minute) / pyunits.ft**3 # regen loading rate -- Minimum brining rate suggested by resin manufacturers to avoid channelling is 0.25 gpm/ft3 of resin, suggest 0.5 to 0.8 (Boodoo Peer Review Comments)
#         regen_reuse = 0  # * pyunits.dimensionless # number of times regen to be reuse; can be reused up to 25 times -- With brine storage/mixing tanks, regenerant may be reused up to 25 times.  Cannot reuse regenerant with salt saturator as the delivery method -- additional tanks would be required.
#         s_rinse_bv = 2  # * pyunits.dimensionless # slow rinse volume
#         f_rinse_bv = 5  # * pyunits.dimensionless $ fast final rinse volume -- 5 to 7 or 3 to 7 bed volumes (Boodoo Peer Review comments).  1 bed volume (Lowry Peer Review comments).
#         f_rinse_rate = 3  # * (pyunits.gallon / pyunits.minute) / pyunits.ft**3 # fast rinse loading rate; equal to backwash loading rate
#         resin_life = 7  # * pyunits.years # useful economic life of resin -- Although regenerated, resin eventually will reach the end of its useful economic life
#         brine_conc_sat = 3.1  # * (pyunits.lb / pyunits.gal) # saturated brine concentration
#         brine_conc = 0.4  # * (pyunits.lb / pyunits.gal) # regen brine concentration -- Designers typically choose a brine concentration that is less than 10%, usually as low as 6% to allow for adequate contact time with the resin during the brining step (Boodoo Peer Review comments)
#         salt_density = 72  # * (pyunits.lbs / pyunits.ft ** 3) #
#         cstore_days = 30  # * pyunits.days # days of chemical storage
#         cmix_hp_per = 0.25  # * (pyunits.hp / (pyunits.kgal)) # chemical tank mixer horsepower
#         mixer_size = 1  # * pyunits.hp
#         resin_loss_annual = 0.045  # * 1 / pyunits.year # annual resin loss due to backwashing?? -- Assume 4 to 5%

#         ############## RESIDUALS DISCHARGE ##############
#         max_waste_ship = 18  # * pyunits.tons # Maximum waste shipment size
#         non_haz_miles = 10  # * pyunits.miles # Miles to non-hazardous solid waste disposal site
#         haz_miles = 200  # * pyunits.miles # Miles to hazardous solid waste disposal site
#         rad_miles = 700  # * pyunits.miles # Miles to radioactive non-hazardous solid waste disposal site
#         hazrad_miles = 700  # * pyunits.miles # Miles to radioactive hazardous solid waste disposal site

#         nonhaz_disposal_cost = 68.20  # $/ton Non-hazardous waste disposal
#         nonhaz_transportation_cost = 0.51  # $/ton*mile Non-hazardous waste transportation
#         haz_disposal_cost = 357.60  # $/ton Hazardous waste disposal
#         haz_trans_min_cost = 3067.09  # $/shipment Hazardous waste minimum charge per shipment
#         haz_transportation_cost = 0.11  # $/ton*mile Hazardous waste transportation
#         hazrad_annual_fee = 1585.06  # $/year Radioactive hazardous waste annual fee
#         hazrad_disposal_cost = 11043.39  # $/ton Radiactive hazardous waste disposal
#         hazrad_trans_min_cost = haz_trans_min_cost
#         hazrad_transportation_cost = 0.26  # $/ton*mile radiactive hazardous waste transportation
#         rad_annual_fee = hazrad_annual_fee  # $/year radiactive waste annual fee
#         rad_disposal_cost = 5145.16  # $/ton radiactive waste disposal
#         rad_transportation_cost = hazrad_transportation_cost  # $/ton*mile radioactive waste transportation
#         rad_trans_min_cost = hazrad_trans_min_cost

#         ########################################################
#         ########################################################
#         ############## O&M ASSUMPTIONS ##############
#         ########################################################
#         ########################################################

#         ############## PUMP ENERGY ##############
#         booster_pump_head = 25  # * pyunits.psi # -- Von Huben, Harry. Operator's Companion, 4th Edition. USABluebook, 2000.  Pp. 17  25 psi creates a head of 60 feet
#         res_pump_psi = 25  # * pyunits.psi
#         booster_pump_efficiency = 0.75
#         backwash_pump_head = 14.7  # * pyunits.psi

#         ########################################################
#         ########################################################
#         ############## VESSEL CONSTRAINTS ##############
#         ########################################################
#         ########################################################

#         ############## FROM INPUTS ##############
#         #self.design_flow = flow_in  # * (pyunits.gallon / pyunits.day) # MGD
#         average_flow = (1 - bp_pct) * flow_in  # MGD
#         design_flow_rate = pyunits.convert(self.flow_vol_in[t], to_units=(pyunits.gallon / pyunits.min))
#         average_flow_rate = average_flow * 1E6 / (24 * 60)  ## convert to gpm .convert(design_flow, to_units=* (pyunits.gallon / pyunits.min)
#         bp_flow_rate = bp_pct / (1 - bp_pct) * design_flow_rate
#         contam = 'SO4'  # targeted contaminant; SO4, NO3, or other

#         num_tanks = 1  # minimum number of vessels in series

#         # options:
#         # Strong base polystyrenic gel-type Type I
#         # Strong base polystyrenic gel-type Type II
#         # Strong base polystyrenic macroporous Type I
#         # Strong base polystyrenic macroporous Type II
#         # Strong base polyacrylic
#         # Nitrate-selective

#         ############## FROM CENTRAL COST DATABASE ##############
#         max_diam = 14  # * pyunits.ft # max diameter for vessel
#         min_diam = 1.5  # * pyunits.ft # min diameter for vessel
#         # max_diam_std_size = 14

#         ############## VESSEL CONSTRAINT VERIFICATION ##############
#         self.ebct_tank = self.ebct[t] / num_tanks
#         if geom == 'vertical':
#             self.max_sa = ((comm_diam - (2 * vessel_thickness)) ** 2 * 3.14159 / 4)  # * pyunits.ft**2 # surface area of vessel- depends on tank_geom
#             distance_above = 0
#             void_above = 0
#         elif geom == 'horizontal':
#             self.max_sa = ((comm_diam - (2 * vessel_thickness)) * comm_height_length)
#             distance_above = comm_diam - bed_depth - horiz_underdrain # * pyunits.ft # Height available above media bed (for horizontal vessels)
#             void_above = comm_height_length * (
#                         comm_diam * comm_diam / 2 * sin((distance_above / comm_diam) ** 0.5) - (comm_diam / 2 - distance_above) * ((comm_diam - distance_above) * distance_above) ** 0.5) # *
#             # pyunits.ft ** 3 # Void space above media bed (for horizontal vessels)


#         ############## QUANTITIES BASED ON USER-SPECIFIED VESSEL DIMENSIONS ##############
#         if geom == 'vertical':
#             comm_sa = ((comm_diam - (2 * vessel_thickness)) ** 2 * 3.14159 / 4)  # * pynits.ft**2 # surface area of vessel- depends on tank_geom
#             self.media_volume = comm_sa * bed_depth  # * pynits.ft**3 # resin volume per vessel
#             self.flow_per_vessel = (self.max_sa * bed_depth * 7.48) / self.ebct_tank  # flow per vessel # depends on tank_geom
#         elif geom == 'horizontal':
#             comm_sa = ((comm_diam - (2 * vessel_thickness)) * comm_height_length)  # * pynits.ft**2 # surface area of vessel- depends on tank_geom
#             self.media_volume = self.comm_vol - horiz_underdrain - void_above  # ft3 - resin volume per vessel
#             self.flow_per_vessel = self.media_volume * 7.48 / self.ebct_tank

#         self.comm_vol = 3.14159 * comm_diam ** 2 / 4 * comm_height_length  # ft3 - total vessel volume
#         self.comm_vol_gal = self.comm_vol * 7.48  # gal - converting from ft3 to gal

#         ############## VESSEL REQUIREMENTS BASED ON BED DEPTH AND CONTACT TIME ##############

#         media_vol_gal = self.media_volume * 7.48  # converting from ft3 to gallons
#         media_per_vessel = self.media_volume * media_density  # * pyunits.lbs  # resin mass per vessel
#         media_volume_expanded = self.media_volume * (1 + bed_expansion)  # ft3 - resin volume when expanded
#         self.num_treat_lines = design_flow_rate / self.flow_per_vessel  # * pyunits.dimensionless # number of treatment trains
#         self.num_redund_vessels = self.num_treat_lines / redund_freq  # number redundant vessles # NEED TO FIGURE OUT HOW TO CALCULATE DYNAMICALLY

#         # self.num_treat_lines = 1  # need to determine dynamically; see above line
#         self.op_num_tanks = self.num_treat_lines * num_tanks  # * pyunits.dimensionless # number of vessels excluding redundancy
#         self.final_num_tanks = self.op_num_tanks + self.num_redund_vessels  # * pyunits.dimensionless # total number of vessels needed
#         total_media = media_per_vessel * self.final_num_tanks  # lbs - total mass of resin needed

#         contact_material = design_flow_rate * self.ebct[t] / 7.481  # * pyunits.ft**3 # vol resin needed

#         resin_load_rate = (design_flow_rate / self.num_treat_lines) / comm_sa  # gpm / ft2 - final surface loading rate
#         contact_mat_per_vessel = contact_material / self.op_num_tanks  # * pyunits.ft**3 # minimum resin per vessel
#         vol_vessel = contact_mat_per_vessel * (1 + bed_expansion)  # * pyunits.ft**3 # minimum vessel vol
#         resin_surf_area = contact_mat_per_vessel / bed_depth  # * pyunits.ft**2 # resin surface area
#         ############## CHECKS ON USER-SPECIFIED DIMENSIONS ##############
#         #### ::: DESIGN DIMENSIONS FOR VERTICAL VESSELS ::: ####
#         height = bed_depth * (1 + bed_expansion) + freeboard  # * pyunits.ft # check on required height of vessel
#         diameter = (resin_surf_area * 4 / 3.14159) ** 0.5 + (2 * vessel_thickness)  # pyunits.ft # check on required diameter of vessel
#         min_comm_height = 4.5  # * pyunits.ft # minimum commercial height given diameter - NEED TO DETERMINE DYNAMICALLY
#         max_comm_height = 15  # * pyunits.ft # maximum commercial height given diameter - NEED TO DETERMINE DYNAMICALLY

#         #### ::: VOID SPACE REQUIRED FOR HORIZONTAL VESSELS ::: ####
#         freeboard_horiz_void = comm_height_length * (
#                 comm_diam * comm_diam / 2 * sin((freeboard / comm_diam) ** 0.5) - (comm_diam / 2 - freeboard) * ((comm_diam - freeboard) * freeboard) ** 0.5)  # * pyunits.ft**3
#         underdrain_horiz_void = comm_height_length * (comm_diam * comm_diam / 2 * sin((horiz_underdrain / comm_diam) ** 0.5) - (comm_diam / 2 - horiz_underdrain) * (
#                 (comm_diam - horiz_underdrain) * horiz_underdrain) ** 0.5)  # * pyunits.ft**3
#         horiz_void = freeboard_horiz_void + underdrain_horiz_void  # * pyunits.ft**3

#         #### ::: VOLUME AVAILABLE FOR MEDIA AND EXPANSION ::: ####
#         vert_vol_avail = (comm_height_length - freeboard) * 3.14159 * comm_diam ** 2 / 4  # * pyunits.ft**3 - volume available for vertical vessel
#         horiz_vol_avail = self.comm_vol - horiz_void  # * pyunits.ft**3 - volume available for horizontal vessel
#         input_vol_vess = 0.40  # * pyunits.dimensionless # tolerance for oversized vessels; possibly could determine dynamically based on tank geometry and flow

#         vol_tol = 0.4

#         ########################################################
#         ########################################################
#         ############## REGEN BACKWASH ##############
#         ########################################################
#         ########################################################

#         ############## FROM INPUTS ##############
#         # bw_pumps = # variable to determine method of backwashing
#         # bw_tanks = # variable to determine method of backwashing

#         ############## RESIN REGENERATION ##############

#         conc_breakthru = 0.1
#         mass_regen = media_per_vessel * self.num_treat_lines * 453.49  # .convert(resin_mass, to_units=pyunits.grams) # mass of resin in grams for Freundlich calc
#         flow_regen = average_flow_rate * 3.785  # .convert(average_flow_rate, to_units=(pyunits.liter / pyunits.minute) # flow rate for Freundlich calc
#         # regen_bed_vol = -606 * np.log(conc_in) + 3150 # bed volumes  # number of bed volumes before regen
#         ## above calculation is dependent on the contaminant of interest
#         ## below calculaation is based on freundlich isotherm
#         regen_bed_vol = (mass_regen * self.freund1 * conc_breakthru ** (1 / self.freund2) / (flow_regen * (self.conc_in - conc_breakthru))) / (
#                     self.media_volume * self.num_treat_lines / average_flow_rate)
#         # media_volume = media_volume / 7.48 # .convert(media_vol, to_units=pyunits.ft**3) # media volume converted back to ft3
#         self.resin_vol_tot = self.media_volume * self.final_num_tanks  # ft3 - total vol of resin needed
#         salt_regen = self.media_volume * salt_dose  # lbs - salt needed per vessel
#         vol_brine_sat = salt_regen / brine_conc_sat  # lbs - volume saturated brine per vessel
#         vol_brine = salt_regen / brine_conc  # gallons - volume dilute brine needed per vessel
#         time_regen = salt_dose / brine_conc / regen_rate  # minutes - time for brine delivery
#         brine_flow = vol_brine / time_regen  # * (pyunits.gallons / pyunits.minute) - dilute brine flow rate
#         regen_days = (self.num_treat_lines * self.media_volume * regen_bed_vol) / (average_flow * 1E6)  # * pyunits.days # regen per vessel freq
#         regen_month = 30 / regen_days  # washes / vessel / month # number of regeneration washes per month
#         salt_store = ((30 / regen_days) * (chem_store / 30)) * salt_regen * self.num_treat_lines / (regen_reuse + 1)  # washes/vessel/month - number of regen washes per month

#         ############## SODIUM CHLORIDE PURCHASING ##############
#         salt_purchase = salt_purchase  # should be able to determine dynamically

#         ############## SALT SATURATORS ##############
#         min_saltbox = 5  # * pyunits.tons # smallest size salt saturator - NEED TO DETERMINE DYNAMICALLY
#         max_saltbox = 79  # * pyunits.tons # largest size salt saturator - NEED TO DETERMINE DYNAMICALLY
#         saltbox_need = 16.87  # * pyunits.tons # needed size salt saturator - NEED TO DETERMINE DYNAMICALLY
#         saltbox_days = 30  # * pyunits.days # days of storage provided by salt saturator - NEED TO DETERMINE DYNAMICALLY
#         num_saltbox = saltbox_need / max_saltbox  # number of saltboxes needed
#         if saltbox_need / num_saltbox < min_saltbox:
#             saltbox_size = min_saltbox  # * pyunits.tons # salt saturator size
#         else:
#             saltbox_size = saltbox_need / num_saltbox
#         eductors = 1  # number of eductors needed - depends on brine disposal method

#         ############## BACKWASH ##############
#         water_flush = backwash_load_rate * comm_sa  # * (pyunits.gallons / pyunits.minute) # backwash flow rate
#         waterflush_vol = water_flush * backwash_time  # * pyunits.gallons # total backwash volume
#         s_rinse_vol = max(media_vol_gal * s_rinse_bv, vol_brine - vol_brine_sat)  # * pyunits.gallons # slow rinse volume
#         s_rinse_gpm = (vol_brine - vol_brine_sat) / time_regen  # * (pyunits.gallons / pyunits.minute) # slow rinse volume
#         s_rinse_time = s_rinse_vol / s_rinse_gpm  # * pyunits.minute # slow rinse time
#         f_rinse_vol = media_vol_gal * f_rinse_bv  # * pyunits.gallons # fast rinse volume
#         f_rinse_time = f_rinse_vol / (f_rinse_rate * comm_sa)  # * pyunits.minute # fast rinse time
#         f_rinse_gpm = f_rinse_vol / f_rinse_time  # * (pyunits.gallons / pyunits.minute) # fast rinse volume
#         self.total_backwash = waterflush_vol + s_rinse_vol + f_rinse_vol  # * pyunits.gallons # total backwash volume
#         max_back_tank_size = 282094  # * pyunits.gallons # maximum backwash tank size - NEED TO DETERMINE DYNAMICALLY
#         self.back_tanks = self.total_backwash / max_back_tank_size  # number of backwash tanks - NEED TO DETERMINE DYNAMICALLY
#         back_tank_vol = self.total_backwash / self.back_tanks  # * pyunits.gallon # backwash tank volume
#         backwash_yr = 365 / regen_days * self.final_num_tanks  # backwashes per year for all vessels - NEED TO DETERMINE DYNAMICALLY

#         ############## BRINE MIXING TANKS ##############
#         regeneration_downtime = backwash_time + s_rinse_time + f_rinse_time  # * pyunits.minutes # regeneration downtime
#         total_downtime = regeneration_downtime * self.final_num_tanks / (24 * 60)  # * pyunits.days # total downtime
#         regen_redun = total_downtime / regen_days  # Number of vessels regenerated at a time
#         max_chem_tank_size = 30000  # * pyunits.gallons # max chemical mixing tank size - NEED TO DETERMINE DYNAMICALLY
#         ## below depends on regen method
#         if vol_brine_sat > max_chem_tank_size:
#             brine_tanks = (vol_brine_sat / max_chem_tank_size) * regen_redun  # number of brine tanks;
#         else:
#             brine_tanks = regen_redun  # number of brine tanks
#         brine_tank_vol = vol_brine_sat * regen_redun / brine_tanks  # * pyunits.gallons # brine tank volume
#         brine_mixers = brine_tank_vol  # number of brine tank mixers

        ########################################################
        ########################################################
        ############## pH ADJUST ##############
        ########################################################
        ########################################################

        ############## FROM INPUTS ##############
        # ph_in = self.conc_mass_in[t, 'ph_min']
        # ph_out = self.conc_mass_out[t, 'ph_min']
        # self.alk_in = pyunits.convert(self.conc_mass_in[t, 'alkalinity_as_caco3'], to_units=(pyunits.mg / pyunits.liter))  # mg / L as CaCO3
        # # self.alk_in = 25
        # tds_in = self.conc_mass_in[t, 'tds']  # * (pyunits.mg / pyunits.liter)
        # temp_in = self.temperature_in[t] # * pyunits.celcius
        # # tds_in = 200
        # # temp_in = 283
        # naoh_soln = 0.5  # * pyunits.dimensionless # Sodium hydroxide weight percent as delivered
        # day_tank_needed = 5  # * pyunits.gallons
        #
        # ionic_strength = tds_in / 40000  # mol / L # 40,000 converts TDS to ionic strength, Equation 4, Trussell 1998
        # temp_var = temp_in - 298  # * pyunits.celcius # For use in Equation S14, Trussell 1998
        # self.dielectric = 78.54 * (1 - 0.004579 * temp_var + 0.0000119 * temp_var ** 2 + 0.000000028 * temp_var ** 3)
        # # temp_in = temp_in + 273.13  # convert from C to K
        # self.a_slope = 1290000 * ((2 ** 0.5 / (self.dielectric * temp_in) ** 1.5))  # Equation S13, Trussell 1998
        # log_gamma_1 = self.a_slope * 1 ** 2 * ((ionic_strength ** 0.5) / (1 + (ionic_strength ** 0.5)) - 0.3 * ionic_strength)  # Modified Davies equation, Equation S12, Trussell 1998
        # log_gamma_2 = self.a_slope * 2 ** 2 * ((ionic_strength ** 0.5) / (1 + (ionic_strength ** 0.5)) - 0.3 * ionic_strength)  # Modified Davies equation, Equation S12, Trussell 1998
        # self.gamma_1 = 10 ** (- log_gamma_1)
        # gamma_2 = 10 ** (- log_gamma_2)
        #
        # # From Table 2, Trussell 1998
        # # From "Lookup Tables" tab in EPA excel model
        #
        # # H2O <-> OH- + H+, Kw
        # kw_a1 = -6.088
        # kw_a2 = 4471
        # kw_a4 = 0.01706
        #
        # # H2CO3 <-> HCO3- + H+, K1
        # k1_a1 = 356.309
        # k1_a2 = -21834.4
        # k1_a3 = -126.834
        # k1_a4 = 0.06092
        # k1_a5 = 1685915
        #
        # # HCO3- <-> CO32- + H+, K2
        # k2_a1 = 107.887
        # k2_a2 = -5151.8
        # k2_a3 = -38.926
        # k2_a4 = 0.032528
        # k2_a5 = 563713.9
        #
        # pk1 = k1_a1 + k1_a2 / temp_in + k1_a3 * log10(temp_in) + k1_a4 * temp_in + k1_a5 / temp_in ** 2  # Equilibrium constant for carbonic acid (H2CO3) (-log form)
        # pk2 = k2_a1 + k2_a2 / temp_in + k2_a3 * log10(temp_in) + k2_a4 * temp_in + k2_a5 / temp_in ** 2  # Equilibrium constant for bicarbonate (HCO3-) (-log form)
        # pkw = kw_a1 + kw_a2 / temp_in + kw_a4 * temp_in  # Equilibrium constant for water (H2O) (-log form)
        #
        # k1 = 10 ** (-pk1)
        # k2 = 10 ** (-pk2)
        # kw = 10 ** (-pkw)
        #
        # self.t1_in = self.gamma_1 * 10 ** -self.ph_in / k1
        # self.t2_in = (self.gamma_1 * k2) / (gamma_2 * 10 ** -self.ph_in )
        # self.t3_in = self.alk_in / 50000
        # self.t4_in = kw / (self.gamma_1 * 10 ** -self.ph_in )
        # self.t5_in = 10 ** -self.ph_in  / self.gamma_1
        # self.t6_in = (2 * k2 * self.gamma_1) / (gamma_2 * 10 ** -self.ph_in )
        #
        # ct_in = (1 + self.t1_in + self.t2_in) * ((self.t3_in - self.t4_in + self.t5_in) / (1 + self.t6_in))
        #
        # t1_f = (2 * k2 * self.gamma_1) / (gamma_2 * 10 ** -self.ph_out)
        # t2_f = (self.gamma_1 * 10 ** -self.ph_out) / k1
        # t3_f = (self.gamma_1 * k2) / (gamma_2 * 10 ** -self.ph_out)
        # t4_f = kw / (self.gamma_1 * 10 ** -self.ph_out)
        # t5_f = 10 ** -self.ph_out / self.gamma_1
        #
        # self.alk_f = 50000 * ((ct_in * (1 + t1_f)) / (1 + t2_f + t3_f) + t4_f - t5_f)  # mg/L as CaCO3 -- Equation 17, Najm 2001, where 50,000 converts eq/L to mg/L
        # # self.conc_mass_out[t, 'alkalinity_as_caco3'] = self.alk_f
        # oh_tot = (self.alk_f - self.alk_in) / 50000  # mol/L -- Equation 20, Najm 2001, where 50,000 converts from mg/L to mol/L
        #
        # naoh_tot = 39.997 * oh_tot * 1000
        # caustic_conc_lb = 6.364  # * (pyunits.lbs / pyunits.gal)
        # lb_naoh_day = 1000000 * 3.7854 * naoh_tot * 2.2 * average_flow / 1000000  # * pyunits.lbs # Pounds of pure NaOH needed per day
        # lb_naoh_store = lb_naoh_day * cstore_days  # * pyunits.lbs #
        # gal_naoh_day = lb_naoh_day / caustic_conc_lb  # * pyunits.gal # Gallons of NaOH needed per day
        # gal_naoh_store = lb_naoh_store / caustic_conc_lb  # # * pyunits.gal # Gallons of NaOH needed in storage
        # des_naoh_flow = gal_naoh_day / 24 * flow_in / average_flow  # Max NaOH flow (based on design flow)
        # naoh_spgr = 1.525  # NaOH solution specific gravity
        # naoh_lbs = gal_naoh_store * naoh_spgr * 8.345  # Total weight of bulk NaOH solution in storage

        ############## FROM INPUTS ##############
        # naoh_tanks = gal_naoh_store / max_chem_tank_size
        # naoh_tank_vol = gal_naoh_store / naoh_tanks # * pyunits.gallons
        # day_tank_vol_needed = 3.7854 * naoh_tot * 2.2 * flow_in / caustic_conc_lb # * pyunits.gallons
        # if value(day_tank_vol_needed < day_tank_needed):
        #     day_tanks = 0
        #     day_tank_vol = 0
        # else:
        #     day_tanks = day_tank_vol_needed / max_chem_tank_size
        #     day_tank_vol = day_tank_vol_needed / day_tanks # * pyunits.gallons

        # _______________________________________________________  # _______________________________________________________  ############## ACTUALLY CALCULATING COST ##############  # _______________________________________________________  # _______________________________________________________

        # CONTACTORS  ## PRESSURE VESSELS
        def fixed_cap():
            def anion_ex_cost_curves(eqn, x):
                cost_df = pd.read_csv('data/an_ex_cost_eqns.csv', index_col='eqn')
                cost_df.drop(columns=['pct_deviation', 'date_modified', 'r_squared', 'max_size', 'min_size'], inplace=True)
                coeffs = dict(cost_df.loc[eqn].items())
                cost = coeffs['C1'] * x ** coeffs['C2'] + coeffs['C3'] * log(x) + coeffs['C4'] + coeffs['C5'] * exp(coeffs['C6'] * x) + coeffs['C7'] * x ** 3 + coeffs['C8'] * x ** 2 + coeffs[
                    'C9'] * x + coeffs['C10']
                return cost

            ### VESSEL COST ###
            pv_ss_cost = anion_ex_cost_curves('ss_pv_eq', self.comm_vol_gal)  # cost of stainless steel pressure vessel
            pv_cs_cost = anion_ex_cost_curves('cs_pv_eq', self.comm_vol_gal)  # cost of carbon steel pressure vessels with stainless internals
            pv_csp_cost = anion_ex_cost_curves('csp_pv_eq', self.comm_vol_gal)  # cost of carbon steel pressure vessels with plastic internals
            pv_fg_cost = anion_ex_cost_curves('fg_pv_eq', self.comm_vol_gal)  # cost of fiberglass pressure vessels
            if pv_material == 'stainless':
                pv_cost = pv_ss_cost * self.num_ix_units_op[t]
            if pv_material == 'carbon with stainless':
                pv_cost = pv_cs_cost * self.num_ix_units_op[t]
            if pv_material == 'carbon with plastic':
                pv_cost = pv_csp_cost * self.num_ix_units_op[t]
            if pv_material == 'fiberglass':
                pv_cost = pv_fg_cost * self.num_ix_units_op[t]
#             resin_type_list = ['styrenic_gel_1', 'styrenic_gel_2', 'styrenic_macro_1', 'styrenic_macro_2', 'polyacrylic', 'nitrate']
            
    
            ### RESIN COST ##
            # Cost taken from 'Cost Data' tab of 'wbs-anion-123017.xlsx'
            # look up table = sba_res_cost_cl                
            self.resin_cap = self.anion_resin_volume[t] * self.resin_cost[t] + self.cation_resin_volume[t] * self.resin_cost[t]
            
            ### BACKWASH TANKS ###
            bw_ss_cost = anion_ex_cost_curves('st_bwt_eq', back_tank_vol)
            bw_fg_cost = anion_ex_cost_curves('fg_bwt_eq', back_tank_vol)
            bw_hdpe_cost = anion_ex_cost_curves('hdpe_bwt_eq', back_tank_vol)
            if bw_tank_type == 'stainless':
                bw_tank_cost = bw_ss_cost * self.back_tanks
            if bw_tank_type == 'fiberglass':
                bw_tank_cost = bw_fg_cost * self.back_tanks
            if bw_tank_type == 'hdpe':
                bw_tank_cost = bw_hdpe_cost * self.back_tanks

            total_system_cost = pv_cost + self.resin_cap + bw_tank_cost

            return total_system_cost * 1E-6

#         @self.Constraint(time, doc="Outlet pressure equation")
#         def outlet_pressure_constraint(self, t):
#             return (self.pressure_in[t] + self.deltaP_outlet[t] == self.pressure_out[t])

#         @self.Constraint(time, doc="Waste pressure equation")
#         def waste_pressure_constraint(self, t):
#             return (self.pressure_in[t] + self.deltaP_waste[t] == self.pressure_waste[t])

#         self.const_list2 = list(self.config.property_package.component_list) #.remove("tds")
#         self.const_list2.remove("tds")

#         for j in self.const_list2:
#             setattr(self, ("%s_eq" % j), Constraint(
#                 expr = self.removal_fraction[t, j] * self.flow_vol_in[t] * self.conc_mass_in[t, j]
#                 == self.flow_vol_waste[t] * self.conc_mass_waste[t, j]
#                 ))

#         def autosize(system_type, flow, num_tanks, num_lines, ebct, ebct_tank, geom='vertical'):

#             def autosize_constraints(system_type, flow=flow, num_tanks=num_tanks, num_lines=num_lines, ebct=ebct, geom=geom):

#                 if system_type == 'pressure':
#                     # vessel surface area
#                     comp_min_sa_vessel = comp_sa_min / num_lines  # based on max load, design flow, and target number of lines
#                     comp_max_sa_vessel = comp_sa_max / num_lines  # based on min load, design flow, and target number of lines

#                     if geom == 'vertical':
#                         # vertical vessel height
#                         comp_min_vert_height = 3  # from reasonable dimensions table
#                         comp_max_vert_height = 14  # from reasonable dimensions table

#                         # vertical bed depth
#                         min_depth_a = comp_vol_required / num_tanks / sa_all_vessels  # ensures that bed depth is sufficient to pass diameter check on vessel design sheet
#                         min_depth_b = min_bed_depth  # from guidance on input sheet
#                         comp_min_vert_bed_depth = max(min_depth_a, min_depth_b)  # strictest of the above
#                         max_depth_a = (max_height - freeboard) / (1 + bed_expansion)  # max bed depth for max_height, given freeboard and bed expansion
#                         max_depth_b = max_bed_depth  # from guidance on input sheet
#                         comp_max_vert_bed_depth = min(max_depth_a, max_depth_b)  # strictest max of the above, rounded

#                         # vertical vessel diameter
#                         min_diam_a = 2 * ((
#                                                   comp_vol_required / num_tanks / 3.14159 / comp_max_vert_bed_depth / num_lines) ** 0.5 + vessel_thickness)  # min diam to avoid bed depth becoming too deep, given required volume
#                         min_diam_b = 2 * ((comp_min_sa_vessel / 3.14159) ** 0.5 + vessel_thickness)  # from min surface area
#                         min_diam_c = 1.5  # from reasonable dimensions table
#                         comp_min_vert_diam = 2 * max(min_diam_a, min_diam_b, min_diam_c), 0 / 2
#                         max_diam_a = 14  # max diameter CDA
#                         max_diam_b = 2 * ((comp_max_sa_vessel / 3.14159) ** 0.5 + vessel_thickness)  # from max surface area
#                         comp_max_vert_diam = max(0.5, 2 * min(max_diam_a, max_diam_b) / 2)  # from reasonable dimensions table

#                         return comp_min_vert_height, comp_max_vert_height, comp_min_vert_diam, comp_max_vert_diam, comp_min_vert_bed_depth, comp_max_vert_bed_depth

#                     if geom == 'horizontal':
#                         # horizontal vessel diameter
#                         comp_min_horiz_diam = 8  # from guidance provided by Bob Dvorin, 5/16/05
#                         comp_max_horiz_diam = min(max_height, max_diam)  # strictest of max_height CDA and max_diam CDA

#                         # horizontal vessel length
#                         min_length_a = comp_min_sa_vessel / (comp_horiz_diam - 2 * vessel_thickness)  # from max load and actual diameter
#                         min_length_b = 20
#                         comp_min_horiz_length = max(min_length_a, min_length_b)
#                         max_length_a = max_length  # max length CDA
#                         max_length_b = comp_max_vol / (comp_horiz_diam * comp_horiz_diam * 3.14159 / 4) / 7.48  # max volume combined with actual diameter
#                         comp_max_horiz_length = min(max_length_a, max_length_b)

#                         # horizontal bed depth
#                         min_depth_a = comp_vol_required / num_tanks / sa_all_vessels  # ensures that bed depth is sufficient for required volume of medium
#                         min_depth_b = min_bed_depth  # from media constraint table
#                         comp_min_horiz_bed_depth = max(min_depth_a, min_depth_b)
#                         max_depth_a = (min(max_height, max_diam) - freeboard) / (1 + bed_expansion)  # max bed depth for max_height or max_diam, given freeboard and bed expansion
#                         max_depth_b = max_bed_depth  # from media constraint table
#                         comp_max_horiz_bed_depth = min(max_depth_a, max_depth_b)

#                         return comp_min_horiz_diam, comp_max_horiz_diam, comp_min_horiz_length, comp_max_horiz_length, comp_min_horiz_bed_depth, comp_max_horiz_bed_depth

#                 if system_type == 'gravity':
#                     # bed depth
#                     min_depth_a = min_depth  # from min_depth CDA
#                     min_depth_b = flow * ebct / (num_lines * 30 * max_width) / 7.48  # assuming max-size contactor and number of contactors above, min depth for sufficient media volume
#                     comp_min_bed_depth_a = max(min_depth_a, min_depth_b)
#                     comp_max_bed_depth_a = max_depth  # from max_depth CDA

#                     # surface area
#                     comp_min_sa_a = flow / num_lines / load_max  # from loading: based on design flow per target line, max loading
#                     comp_max_sa_a = flow / num_lines / load_min  # from loading: based on design flow per target line, min loading

#                     # contactor length
#                     comp_min_length_a = 6  # from min_length CDA
#                     comp_max_length_a = 30  # from max_length CDA

#                     # contactor width
#                     comp_min_width_a = min_width  # from min_width CDA
#                     comp_max_width_a = max_width  # from max_width CDA

#                     return comp_min_bed_depth_a, comp_max_bed_depth_a, comp_min_sa_a, comp_max_sa_a, comp_min_length_a, comp_max_length_a, comp_min_width_a, comp_max_width_a

#                 ## PRESSURE ##

#             if system_type == 'pressure':

#                 comp_vol_required_stg1 = flow * ebct_tank / 7.48  # volume of media in first-stage vessels
#                 comp_sa_min = flow / load_max  # to reach maximum loading rate
#                 comp_sa_max = flow / load_min  # to reach minimum loading rate
#                 comp_vol_required = flow * ebct / 7.481  # volume of media in all vessels

#                 if geom == 'vertical':
#                     comp_target_bed_depth_vert = target_bed_depth_over  # based on target load CDA
#                     comp_sa_required_vert = comp_vol_required_stg1 / comp_target_bed_depth_vert  # based on media volume and bed depth
#                     comp_vert_diam = 2 * ((comp_sa_required_vert / num_lines / 3.14159) ** 0.5 + vessel_thickness)  # target diameter
#                     sa_one_vessel = (comp_vert_diam - 2 * vessel_thickness) * (comp_vert_diam - 2 * vessel_thickness) * 3.14159 / 4  # surface area, one vessel
#                     sa_all_vessels = sa_one_vessel * num_lines  # surface area, all vessels

#                     comp_min_vert_height, comp_max_vert_height, comp_min_vert_diam, comp_max_vert_diam, comp_min_vert_bed_depth, comp_max_vert_bed_depth = autosize_constraints(system_type, geom=geom)

#                     # vertical design search
#                     comp_vert_max_media = (comp_max_vert_diam / 2 - vessel_thickness) * (
#                             comp_max_vert_diam / 2 - vessel_thickness) * 3.14159 * comp_max_vert_bed_depth  # based on guidance and CDAs for max dimensions
#                     comp_vert_max_sa = (max_diam / 2 - vessel_thickness) * (max_diam / 2 - vessel_thickness) * 3.14159  # based on max_diam CDA

#                     num_lines_vert_a = comp_sa_min / comp_vert_max_sa  # based on surface area from max load
#                     num_lines_vert_b = comp_sa_required_vert / comp_vert_max_sa  # based on surface area from bed depth
#                     num_lines_vert_c = comp_vol_required_stg1 / comp_vert_max_media  # based on media volume
#                     comp_vert_min_number = max(num_lines_vert_a, num_lines_vert_b, num_lines_vert_c)

#                     # inputs

#                     comp_vert_bed_depth = comp_vol_required / num_tanks / sa_all_vessels  # bed depth
#                     comp_vert_height = (1 + bed_expansion) * comp_vert_bed_depth + freeboard  # target height
#                     comp_bed_depth = comp_vert_bed_depth  # bed depth for chosen geometry

#                     if comp_vert_diam < comp_min_vert_diam:
#                         comp_vert_diam = comp_min_vert_diam
#                     elif comp_vert_diam > comp_max_vert_diam:
#                         comp_vert_diam = comp_max_vert_diam
#                     else:
#                         comp_vert_diam = 2 * comp_vert_diam / 2

#                     if comp_min_vert_bed_depth <= comp_max_vert_bed_depth:
#                         if comp_bed_depth < comp_min_vert_bed_depth:
#                             comp_bed_depth = comp_min_vert_bed_depth
#                         elif comp_bed_depth > comp_max_vert_bed_depth:
#                             comp_bed_depth = comp_max_vert_bed_depth
#                         else:
#                             comp_bed_depth = comp_vert_bed_depth

#                     if comp_min_vert_height > comp_max_vert_height:
#                         comp_vert_height = -1
#                         print(f'Min vert height greater than max vert height.\n\tcomp_min_vert_height = {comp_min_vert_height}\n\tcomp_max_vert_height = {comp_max_vert_height}')
#                         print('I am not sure what this means yet.')
#                     elif comp_vert_height > comp_max_vert_height:
#                         comp_vert_height = comp_max_vert_height
#                     elif comp_vert_height < comp_min_vert_height:
#                         comp_vert_height = 2 * comp_vert_height / 2  ## NEED TO HAVE A ROUNDUP FUNCTION HERE

#                     return comp_vert_min_number, comp_vert_height, comp_bed_depth, comp_vert_diam

#                 if geom == 'horizontal':

#                     comp_min_horiz_diam, comp_max_horiz_diam, comp_min_horiz_length, comp_max_horiz_length, comp_min_horiz_bed_depth, comp_max_horiz_bed_depth = autosize_constraints(system_type,
#                                                                                                                                                                                       geom=geom)
#                     # inputs
#                     comp_max_vol = 27100  # max pressure vessel volume LOOKED UP
#                     comp_max_vol_length = comp_max_vol / 7.48 / (3.14159 * comp_max_horiz_diam * comp_max_horiz_diam / 4)  # rounded to reflect the length we will actually use on the input sheet
#                     comp_target_bed_depth_horiz = target_bed_depth_horiz  # based on target load CDA
#                     comp_sa_required_horiz = comp_vol_required_stg1 / comp_target_bed_depth_horiz  # based on media volume and bed depth

#                     fb = comp_max_vol_length * (comp_max_horiz_diam * comp_max_horiz_diam / 2 * np.arcsin((freeboard / comp_max_horiz_diam) ** 0.5) - (comp_max_horiz_diam / 2 - freeboard) * (
#                             (comp_max_horiz_diam - freeboard) * freeboard) ** 0.5)  # freeboard - volume of a horizontal slice of a cylinder
#                     ud = comp_max_vol_length * (
#                             comp_max_horiz_diam * comp_max_horiz_diam / 2 * np.arcsin((horiz_underdrain / comp_max_horiz_diam) ** 0.5) - (comp_max_horiz_diam / 2 - horiz_underdrain) * (
#                             (comp_max_horiz_diam - horiz_underdrain) * horiz_underdrain) ** 0.5)  # underdrain
#                     comp_horiz_void_required = fb + ud  # total of the two void volumes above
#                     comp_horiz_void_area = comp_horiz_void_required / comp_max_vol_length  # assumed void volume per length
#                     comp_horiz_expanded_bd = comp_target_bed_depth_horiz * (1 + bed_expansion)  # target bed depth after expansion
#                     comp_horiz_diam = (comp_horiz_expanded_bd + (comp_horiz_expanded_bd * comp_horiz_expanded_bd + 3.14159 * comp_horiz_void_area) ** 0.5) / (3.14159 / 2)  # target diameter
#                     # comp_horiz_diam_old = (comp_sa_required_horiz / num_lines / length_diam_ratio) ** 0.5
#                     comp_horiz_length = comp_sa_required_horiz / (comp_horiz_diam - 2 * vessel_thickness) / num_lines  # target length
#                     sa_all_vessels = num_lines * (comp_horiz_diam - 2 * vessel_thickness) * comp_horiz_length  # surface area for all vessels
#                     comp_horiz_bed_depth = comp_vol_required / num_tanks / sa_all_vessels
#                     comp_bed_depth = comp_horiz_bed_depth  # bed depth for chosen geometry

#                     # horizontal design search

#                     comp_max_horiz_sa = (comp_max_horiz_diam - 2 * vessel_thickness) * comp_max_vol_length  # max vessel surface area
#                     comp_target_bed_depth_horiz = target_bed_depth_horiz  # based on target load CDA -- NEEDS TO BE ADJUSTABLE FOR FLOW AND INCLUSION OF UV AOP
#                     comp_sa_required_horiz = comp_vol_required_stg1 / comp_target_bed_depth_horiz  # total vessel surface area, based upon media volume and ved depth

#                     comp_horiz_max_media = (comp_max_vol / 7.481 - comp_horiz_void_required) / (1 + bed_expansion)  # max media volume
#                     num_lines_horiz_a = comp_sa_min / comp_max_horiz_sa  # based on surface area from max load
#                     num_lines_horiz_b = comp_sa_required_horiz / comp_max_horiz_sa  # based on surface area from bed depth
#                     num_lines_horiz_c = comp_vol_required_stg1 / comp_horiz_max_media  # based on media volume
#                     comp_horiz_min_number = max(num_lines_horiz_a, num_lines_horiz_b, num_lines_horiz_c)  # min number of lines, horizontal vessels

#                     if comp_min_horiz_diam <= comp_max_horiz_diam:
#                         if comp_horiz_diam < comp_min_horiz_diam:
#                             comp_horiz_diam = comp_min_horiz_diam
#                         elif comp_horiz_diam > comp_max_horiz_diam:
#                             comp_horiz_diam = comp_max_horiz_diam
#                         else:
#                             comp_horiz_diam = 2 * comp_horiz_diam / 2  ##  NEED ROUND UP FUNCtiON HERE

#                     if comp_min_horiz_length <= comp_max_horiz_length:
#                         if comp_horiz_length < comp_min_horiz_length:
#                             comp_horiz_length = comp_min_horiz_length
#                         elif comp_horiz_length > comp_max_horiz_length:
#                             comp_horiz_length = comp_max_horiz_length
#                         else:
#                             comp_horiz_length = comp_horiz_length

#                     return comp_max_horiz_sa, comp_horiz_length, comp_bed_depth, comp_horiz_min_number

#             if system_type == 'gravity':
#                 comp_min_bed_depth_a, comp_max_bed_depth_a, comp_min_sa_a, comp_max_sa_a, comp_min_length_a, comp_max_length_a, comp_min_width_a, comp_max_width_a = autosize_constraints(system_type,
#                                                                                                                                                                                           geom=geom)

#                 comp_vol_required_a = flow * ebct / 7.481  # volume of media in all vessels
#                 # design search
#                 comp_vert_max_media_a = comp_max_bed_depth_a * comp_max_length_a * comp_max_width_a  # based on guidance and CDAs for max dimensions
#                 comp_sa_min_a = flow / load_max  # to reach maximum loading rate
#                 comp_sa_max_a = flow / load_min  # to reach minimum loading rate
#                 comp_target_bed_depth_vert_a = target_bed_depth_over  ## based on Target Bed Depth CDA -- NEEDS TO BE ADJUSTABLE FOR SMALLER FLOWS AND INCLUSION (OR NOT) OF UV AOP... SEE DOCUMENTATION AND EXCEL SHEET
#                 comp_sa_required_vert_a = comp_vol_required_a / comp_target_bed_depth_vert_a  # based on media volume and bed depth
#                 num_lines_grav_a = comp_min_sa_a / comp_sa_max_a
#                 num_lines_grav_b = comp_sa_required_vert_a / comp_sa_max_a
#                 num_lines_grav_c = comp_vol_required_a / comp_vert_max_media_a
#                 comp_vert_min_number_a = min(num_lines_grav_a, num_lines_grav_b, num_lines_grav_c)  # below this number of lines, we are constrained to horizontal vessels

#                 comp_length_width_a = (comp_sa_required_vert_a / num_lines) ** 0.5  # target side length
#                 sa_one_vessel = comp_length_width_a ** 2  # surface area one vessel
#                 sa_all_vessels = num_lines * sa_one_vessel  # surface area all vessels
#                 comp_bed_depth_a = comp_vol_required_a / num_tanks / sa_all_vessels  # bed depth

#                 if comp_length_width_a < comp_min_length_a:
#                     comp_length_width_a = comp_min_length_a
#                 elif comp_length_width_a > comp_max_length_a:
#                     comp_length_width_a = 2 * comp_length_width_a / 2  ## NEED ROUND UP FUNCTION HERE=

#                 return comp_length_width_a, comp_bed_depth_a, comp_vert_min_number_a

        chem_dict = {}
        self.chem_dict = chem_dict

        def electricity(flow_in):  # m3/hr
            flow_in = pyunits.convert(flow_in, to_units=(pyunits.m ** 3 / pyunits.year))

            electricity = (750 * 1E3) / flow_in  # kWh/m3

            return electricity

        ## fixed_cap_inv_unadjusted ##
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(), doc="Unadjusted fixed capital investment")  # $M

        ## electricity consumption ##
        self.electricity = electricity(flow_in)  # kwh/m3

        ##########################################
        ####### GET REST OF UNIT COSTS ######
        ##########################################

        module.get_complete_costing(self.costing)
