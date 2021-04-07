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
module_name = "gac"

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
        global res_stagger_time, num_treat_lines, water_flush, basin_op_depth, tss_residuals, res_flow_annual, transport_min, disposal_miles, transport_unit, disposal
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
        # time = self.flowsheet().config.time.first()

        # t = self.flowsheet().config.time.first()
        time = self.flowsheet().config.time

        # get tic or tpec (could still be made more efficent code-wise, but could enough for now)
        sys_cost_params = self.parent_block().costing_param
        self.costing.tpec_tic = sys_cost_params.tpec if tpec_or_tic == "TPEC" else sys_cost_params.tic
        tpec_tic = self.costing.tpec_tic
        # basis year for the unit model - based on reference for the method.
        self.costing.basis_year = unit_basis_yr
        # system_type = unit_params
        # ebct_init = Block()
        self.ebct = Var(time, initialize=unit_params['ebct'], domain=NonNegativeReals, bounds=(1, 30),  # units=pyunits.dimensionless,
                        doc="ebct")
        # self.ebct.fix(unit_params['ebct'])
        time = self.flowsheet().config.time.first()
        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.Mgallons / pyunits.day)

        system_type = unit_params['system_type']
        # regen = unit_params['regen']
        regen = 'onsite'
        try:
            self.freund1 = unit_params['freund1']  # Kf (ug/g)(L/ug)1/n
            self.freund2 = unit_params['freund2']  # dimensionless
            self.conc_in = unit_params['conc_in']
            self.conc_breakthru = unit_params['conc_breakthru']
        except:
            # defaults to values for Atrazine and 99% reduction (1 mg/L --> 0.01 mg/L)
            self.freund1 = 38700
            self.freund2 = 0.291
            self.conc_in = 1
            self.conc_breakthru = 0.01

        # if system_type == 'pressure':
        # geom should be determined by autosize function
        # or should be able to be determined by autosize function
        try:
            geom = unit_params['geom']
            pv_material = unit_params['pv_material']
            bw_tank_type = unit_params['bw_tank_type']
        except:
            geom = 'vertical'
            pv_material = 'stainless'
            bw_tank_type = 'stainless'

        # TODO -->> ADD THESE TO UNIT self.X

        #### CHEMS ###

        ############## SYSTEM INPUTS ##############
        #     flow_in = 1
        bp_pct = 0  # * pyunits.dimensionless # bypass percent of flow
        comm_diam = 8.5  # * pyunits.ft # vessel diameter ??
        vessel_thickness = 0  # * pyunits.ft # thickness of vessel walls ?
        comm_height_length = 11  # * pyunits.ft # "straight" height of vessel ??
        bed_depth = 6.7  # * pyunits.ft # vessel bed depth
        backwash_load_rate = 3  # * (pyunits.gallon / pyunits.minute) / pyunits.ft**2 # backwash loading rate
        backwash_time = 12  # * pyunits.minutes # backwashing time
        backwash_interval = 168  # * pyunits.hours # interval between backwash occurrences, depends on many things # 48 hours for surface water if loading rate 4-6 gpm/sf; 7+ days for ground water (Richard E. Hubel, Peter Keenan, American Water Works Service Company, Inc).  2 weeks or loss of head based on operational experience (Verna Arnette, Greater Cincinnati Water Works).
        regen_list = ['onsite', 'offsite', 'throw_nonhaz', 'offsite_haz', 'throw_haz', 'throw_rad', 'throw_hazrad']
        pv_material_list = ['stainless', 'carbon with stainless', 'carbon with plastic', 'fiberglass']
        #     regen = 'onsite'

        ########################################################
        ########################################################
        ############## CRITICAL DESIGN ASSUMPTIONS ##############
        ########################################################
        ########################################################

        ############## GAC CONTACTOR DESIGN ##############
        bed_expansion = 0.5  # * pyunits.dimensionless # resin expansion during backwash
        load_min = 0.5  # gpm / ft2, # Hydraulic surface loading rate determines headloss and is usually kept between 2 -10 gpm/sf. Higher loading rates OK if hydraulics and tests allow. Typical hydraulic design criteria are a surface loading rate of 2-10 gpm/ft2 (Montgomery, James M.  Water Treatment Principles and Design.  New York: John Wiley and Sons, 1985. Pp. 553.)  Most regulatory agencies will not approve rates in excess of 2 gpm/ft2 without successful pilot-scale testing (American Water Works Association and American Society of Civil Engineers. Water Treatment Plant Design. Third Edition. New York: McGraw Hill, 1998. Pp. 158.).
        load_max = 10  # gpm / ft2, # Many systems can operate to 0.5 gpm/sf (Richard E. Hubel, Peter Keenan, American Water Works Service Company, Inc.).

        ############## PRESSURE VESSEL DESIGN ##############
        if system_type == 'pressure':
            max_height = 14  # * pyunits.ft
            max_length = 53  # * pyunits.ft
            freeboard = 0.5  # * pyunits.ft # free board above media at full expansion
            horiz_underdrain = 1.5  # * pyunits.ft # underdrain space for horizontal vessels
            length_diam_ratio = 2.5
            min_bed_depth = 2  # * pyunits.ft # Typical pressure GAC bed depths are 2-8.5 ft
            max_bed_depth = 8.5  # * pyunits.ft
            target_bed_depth_under = 4  # * pyunits.ft # pressure designs < 1MGD
            target_bed_depth_over = 7  # * pyunits.ft # pressure designs > 1MGD
            target_bed_depth_horiz = 8  # * pyunits.ft # horizontal designs

        ############## GRAVITY BASIN DESIGN ##############
        if system_type == 'gravity':
            max_length = 30  # * pyunits.ft
            min_length = 6  # * pyunits.ft
            max_width = 30  # * pyunits.ft
            min_width = 6  # * pyunits.ft
            max_depth = 10  # * pyunits.ft
            min_depth = 3  # * pyunits.ft # Typical gravity GAC bed depths are 3-10 ft
            freeboard = 2  # * pyunits.ft # free board above media at full expansion
            target_bed_depth_under = 6  # * pyunits.ft # gravity designs < 1MGD
            target_bed_depth_uv_aop = 5.4  # * pyunits.ft # gravity with UV AOP no matter flow
            target_bed_depth_over = 8  # * pyunits.ft # pressure designs > 1MGD

        ############## GENERAL FOR ALL BASINS ##############
        num_stairs = 15  # only if concrete used
        overexcavate = 4  # * pyunits.ft # 2 feet each side in each dimension. This assumption used only if concrete basins are used.
        conc_thick = 1  # * pyunits.ft # This assumption used only if concrete basins are used

        ############## PUMPING ##############
        pump_safety_factor = 0.25  # * pyunits.dimensionless # safety factor for pumps
        num_redund_pumps = 1  # number of redundant pumps
        num_redund_back_pumps = 1
        num_pumps = 1

        ############## BACKWASH ##############
        backwash_rate = 12  # * pyunits.gallon / pyunits.minute / pyunits.ft ** 2 # Fluidization occurs at 2-4 gpm/sf; 12-15 gpm/sf is needed to "expand" GAC and wash out particulates [Calgon Carbon] (Richard E. Hubel, Peter Keenan, American Water Works Service Company, Inc)
        backwash_time = 10  # * pyunits.minute # Backwash duration is time allowed for backwash of filter. Use highest expected duration. Typically 5-10 minutes. Default is 10 minutes.
        back_multiplier = 1  # volume # number of backwash ctcles to provide a storage volume for clean water
        back_ratio = 0.6  # only if concrete basins are used
        back_freeboard = 3  # * pyunits.ft # only if concrete basins are  used

        ############## GAC REGENERATION AND TRANSFER ##############
        gac_density = 30  # * pyunits.lb / pyunits.ft ** 3 # Bulk density, not particle density. GAC density range of 22-30 lb/cubic ft; lignite GAC approximately 22 and bituminous GAC approximately 28 lb/cubic ft (Randal J. Braker, General Manager, Duck River Utility Commission)
        regen_runtime = 0.85  # Percent of time that regeneration facility operates. Less than full time (100%) to allow for routine maintenance.
        regen_redund = 1  # 100% means no redundancy (i.e., no additional capacity beyond that needed to account for runtime). Use a value greater than 100% to add capacity and provide redundancy.
        makeup_rate = 0.1  # Makeup carbon 10% for on-site regeneration (Richard E. Hubel, Peter Keenan, American Water Works Service Company).
        makeup_rate_off = 0.3  # Makeup carbon needs are higher for transport and regeneration off-site -- 30% (Richard E. Hubel, Peter Keenan, American Water Works Service Company).
        transfer_time = 4  # * pyunits.hours # Time to empty GAC bed; for mechanical transfer only
        transfer_time_hold = 4  # * pyunits.hours # Time to empty holding tank/basin soilds; for mechanical transfer only
        virgin_gac_storage = 1.33  # bed volumes
        spent_gac_storage = 1.33
        regen_gac_storage = 1.33
        storage_basins = 1  # Default: one each for virgin, spent, and regenerated GAC. This assumption applies if concrete basins are used. If steel tanks are used, number calculated on regeneration sheet.
        storage_ratio = 0.6  # only if concrete used
        storage_freeboard = 3  # * pyunits.ft # only if concrete used

        ########################################################
        ########################################################
        ############## CONTACTOR CONSTRAINTS ##############
        ########################################################
        ########################################################

        ############## FROM INPUTS ##############
        design_flow = flow_in  # MGD
        average_flow = (1 - bp_pct) * design_flow  # MGD
        # design_flow_rate = design_flow * 1E6 / (24 * 60)  ## convert to gpm  .convert(design_flow, to_units=* (pyunits.gallon / pyunits.min)
        design_flow_rate = pyunits.convert(design_flow, to_units=(pyunits.gallon / pyunits.min))
        # average_flow_rate = average_flow * 1E6 / (24 * 60)  ## convert to gpm .convert(design_flow, to_units=* (pyunits.gallon / pyunits.min)
        average_flow_rate = pyunits.convert(average_flow, to_units=(pyunits.gallon / pyunits.min))

        bp_flow_rate = bp_pct / (1 - bp_pct) * design_flow_rate  # gpm - bypass flowrate
        target_contaminant = 'test'  #
        #     conc_in = 10  # * (pyunits.mg / pyunits.L) # influent concentration of target contaminant
        #     conc_out = 1  # * (pyunits.mg / pyunits.L) # target effluent concentration of target contaminant
        #     conc_breakthru = 5  # * (pyunits.mg / pyunits.L) # breakthrough concentration
        #     kss = 0.01  # * pyunits.hour ** -1 # steady state system constant
        #     ebct = (np.log(conc_in / conc_out) / kss) * 60  # * pyunits.min # calculated EBCT based on Kss - conc_out/conc_in = exp(-kss * ebct)
        #     ebct = 4  # * pyunits.min # empty bed contact time - INPUT

        if system_type == 'pressure':
            ############## PRESSURE VESSELS ##############
            num_vessels = 1

            ############## FROM CENTRAL COST DATABASE ##############
            max_diam = 14  # * pyunits.ft # max diameter for vessel
            min_diam = 1.5  # * pyunits.ft # min diameter for vessel

            ############## VESSEL REQUIREMENTS BASED ON BED DEPTH AND CONTACT TIME ##############
            contact_material = design_flow_rate * self.ebct[time] / 7.481  # * pyunits.ft ** 3 # minimum contact material needed

            ############## QUANTITIES BASED ON USER-SPECIFIED VESSEL DIMENSIONS ##############

            comm_vol = 3.14159 * comm_diam ** 2 / 4 * comm_height_length  # ft3 - total vessel volume

            ############## CHECKS ON USER-SPECIFIED DIMENSIONS ##############
            #### ::: DESIGN DIMENSIONS FOR VERTICAL VESSELS ::: ####
            height = bed_depth * (1 + bed_expansion) + freeboard  # * pyunits.ft # check on required height of vessel
            min_comm_height = 6  # * pyunits.ft # minimum commercial height given diameter - NEED TO DETERMINE DYNAMICALLY
            max_comm_height = 20  # * pyunits.ft # maximum commercial height given diameter - NEED TO DETERMINE DYNAMICALLY

            #### ::: VOID SPACE REQUIRED FOR HORIZONTAL VESSELS ::: ####
            freeboard_horiz_void = comm_height_length * (
                    comm_diam * comm_diam / 2 * np.arcsin((freeboard / comm_diam) ** 0.5) - (comm_diam / 2 - freeboard) * ((comm_diam - freeboard) * freeboard) ** 0.5)
            underdrain_horiz_void = comm_height_length * (comm_diam * comm_diam / 2 * np.arcsin((horiz_underdrain / comm_diam) ** 0.5) - (comm_diam / 2 - horiz_underdrain) * (
                    (comm_diam - horiz_underdrain) * horiz_underdrain) ** 0.5)  # * pyunits.ft**3
            horiz_void = freeboard_horiz_void + underdrain_horiz_void  # * pyunits.ft**3

            #### ::: VOLUME AVAILABLE FOR MEDIA AND EXPANSION ::: ####
            vert_vol_avail = (comm_height_length - freeboard) * 3.14159 * comm_diam ** 2 / 4  # * pyunits.ft**3 - volume available for vertical vessel
            horiz_vol_avail = comm_vol - horiz_void  # * pyunits.ft**3 - volume available for horizontal vessel
            vol_tol = 0.40  # * pyunits.dimensionless # tolerance for oversized vessels; possibly could determine dynamically based on tank geometry and flow
            ebct_tank = self.ebct[time] / num_vessels
            distance_above = 0  # pyunits.ft # height available above media bed for horizontal vessels
            void_above = 0  # * pyunits.ft**3 # void space above media bed for horizontal vessels
            if geom == 'vertical':
                self.max_sa = ((comm_diam - (2 * vessel_thickness)) ** 2 * 3.14159 / 4)  # * pynits.ft**2 # surface area of vessel- depends on tank_geom
                self.media_vol = (self.max_sa * bed_depth)  # * pyunits.ft ** 3 # GAC volume per contactor
                flow_per_vessel = (self.media_vol * 7.48) / ebct_tank  # flow per vessel # depends on tank_geom
            if geom == 'horizontal':
                self.max_sa = ((comm_diam - (2 * vessel_thickness)) * comm_height_length)  # * pynits.ft**2 # surface area of vessel- depends on tank_geom
                self.media_vol = (comm_vol - underdrain_horiz_void - void_above)  # * pyunits.ft ** 3 # GAC volume per contactor
                flow_per_vessel = (self.media_vol * 7.48) / ebct_tank
            # num_treat_lines = math.ceil(design_flow_rate / flow_per_vessel)  # * pyunits.dimensionless # number of treatment trains
            num_treat_lines = design_flow_rate / flow_per_vessel  # * pyunits.dimensionless # number of treatment trains

            #     num_treat_lines = design_flow_rate / flow_per_vessel  # need to determine dynamically; see above line
            # self.op_num_tanks = math.ceil(num_treat_lines * num_vessels)  # * pyunits.dimensionless # number of vessels excluding redundancy
            self.op_num_tanks = num_treat_lines * num_vessels  # * pyunits.dimensionless # number of vessels excluding redundancy

            num_redund_tanks = 1  # number redundant vessles # NEED TO FIGURE OUT HOW TO CALCULATE DYNAMICALLY
            self.tot_num_tanks = self.op_num_tanks + num_redund_tanks  # * pyunits.dimensionless # total number of vessels needed
            contact_mat_per_vessel = contact_material / self.op_num_tanks
            min_sa = contact_mat_per_vessel / bed_depth
            diameter = (min_sa * 4 / 3.14159) ** 0.5 + (2 * vessel_thickness)  # pyunits.ft # check on required diameter of vessel
            self.gac_each = self.media_vol * gac_density  # * pyunits.lb # GAC quantity each contactor
            self.gac_total = self.gac_each * self.tot_num_tanks
            gac_expand = self.media_vol * (1 + bed_expansion)

        if system_type == 'gravity':
            ############## GRAVITY CONTACT BASINS ##############
            self.min_basin_vol = design_flow_rate * self.ebct[time] / 7.48  # * pyunits.ft ** 3
            basin_freeboard = 2  # * pyunits.ft # Basin freeboard above filter media at full expansion
            self.basin_width = 8  # * pyunits.ft
            self.basin_length = self.basin_width
            basin_op_depth = 7.9  # * pyunits.ft
            basin_depth = basin_op_depth * (1 + bed_expansion) + basin_freeboard
            num_redund_basins = 1  # number redundant basins # NEED TO FIGURE OUT HOW TO CALCULATE DYNAMICALLY
            # self.op_num_basins = math.ceil(self.min_basin_vol / (self.basin_width * self.basin_length * basin_op_depth))
            self.op_num_basins = self.min_basin_vol / (self.basin_width * self.basin_length * basin_op_depth)

            self.tot_num_basins = num_redund_basins + self.op_num_basins
            basin_conc_vol = (2 * (self.basin_width * self.tot_num_basins + conc_thick * (self.tot_num_basins + 1)) * basin_depth * conc_thick + (
                        self.tot_num_basins + 1) * self.basin_length * basin_depth * conc_thick + (self.basin_length + 2 * conc_thick) * (
                                          self.basin_width * self.tot_num_basins + conc_thick * (self.tot_num_basins + 1)) * conc_thick) / 27  # * pyunits.yard ** 3 # concrete vol for contact basins
            excavation_vol = ((self.tot_num_basins * self.basin_width + (self.tot_num_basins + 1) * conc_thick + overexcavate) * (self.basin_length + 2 * conc_thick + overexcavate) * (
                    basin_depth + conc_thick + overexcavate) + 0.5 * (3 * (basin_depth + conc_thick + overexcavate) * (basin_depth + conc_thick + overexcavate) * (
                    self.basin_length + 2 * conc_thick + overexcavate))) / 27  # * pyunits.yard ** 3 # concrete excavation vol for contact basins
            backfill_vol = excavation_vol - (self.tot_num_basins * self.basin_width + (self.tot_num_basins + 1) * conc_thick) * (self.basin_length + 2 * conc_thick) * (basin_depth + conc_thick) / 27
            railing = 2 * (self.tot_num_basins * self.basin_width + 2 * conc_thick / 2 + (self.tot_num_basins - 1) * conc_thick) + 2 * (
                        self.basin_length + 2 * conc_thick / 2)  # * pyunits.ft # railing length for contact basins
            self.basin_area = self.basin_width * self.basin_length  # * pyunits.ft ** 2 # surface area for each contactor
            loading_rate = design_flow_rate / (self.op_num_basins * (self.basin_width * self.basin_length))  # * pyunits.gallon / pyunits.minute / pyunits.ft ** 2 # basin loading rate
            self.media_vol = self.basin_width * basin_op_depth * self.basin_length
            self.gac_each = self.media_vol * gac_density  # * pyunits.lb # GAC quantity each contactor
            self.gac_total = self.gac_each * self.tot_num_basins
            gac_expand = self.media_vol * (1 + bed_expansion)

        ############## MEDIA QUANTITIES ##############

        media_vol_expanded = self.media_vol * (1 + bed_expansion)

        ########################################################
        ########################################################
        ############## BACKWASH AND REGENERATION ##############
        ########################################################
        ########################################################

        ############## FROM INPUTS ##############
        bw_pumps = 1  # variable to determine method of backwashing
        bw_tanks = 1  # variable to determine method of backwashing
        storage_basins = 1  # how many storage basins do you want for each of virgin, spent, regen GAC

        ############## BACKWASH ##############
        if system_type == 'pressure':
            water_flush = backwash_rate * self.max_sa  # * (pyunits.gallons / pyunits.minute) # backwash flow rate
        if system_type == 'gravity':
            water_flush = backwash_rate * self.basin_width * self.basin_length  # * (pyunits.gallons / pyunits.minute) # backwash flow rate
        total_backwash = water_flush * backwash_time  # * pyunits.gallons # total backwash volume
        backwash_storage = total_backwash * back_multiplier / 7.48  # * pyunits.ft ** 3 # backwash storage volume
        num_back_basins = 1  # default value, number of backwash basins
        back_basin_op_depth = (backwash_storage / num_back_basins) ** (1 / 3) * back_ratio  # * pyunits.ft # operational depth
        back_basin_width = ((total_backwash / num_back_basins) / back_basin_op_depth) ** 0.5
        back_basin_length = back_basin_width
        back_basin_depth = back_basin_op_depth + back_freeboard  # * pyunits.ft # total depth including freeboard
        back_basin_vol = back_basin_width * back_basin_length * back_basin_depth * 7.48  # pyunits.gallons # backwash basin volume
        back_conc_vol = (2 * (back_basin_width * num_back_basins + conc_thick * (num_back_basins + 1)) * back_basin_depth * conc_thick + (
                num_back_basins + 1) * back_basin_length * back_basin_depth * conc_thick + (back_basin_length + 2 * conc_thick) * (
                                 back_basin_width * num_back_basins + conc_thick * (num_back_basins + 1)) * conc_thick) / 27  # * pyunits.yards ** 3 # Concrete volume
        back_excavation_vol = ((num_back_basins * back_basin_width + (num_back_basins + 1) * conc_thick + overexcavate) * (back_basin_length + 2 * conc_thick + overexcavate) * (
                back_basin_depth + conc_thick + overexcavate) + 0.5 * (3 * (back_basin_depth + conc_thick + overexcavate) * (back_basin_depth + conc_thick + overexcavate) * (
                back_basin_length + 2 * conc_thick + overexcavate))) / 27  # * pyunits.yards ** 3 # Excavation volume
        back_backfill_vol = back_excavation_vol - (num_back_basins * back_basin_width + (num_back_basins + 1) * conc_thick) * (back_basin_length + 2 * conc_thick) * (
                back_basin_depth + conc_thick) / 27  # * pyunits.yards ** 3 # Backfill volume
        back_railing = 2 * (num_back_basins * back_basin_width + 2 * conc_thick / 2 + (num_back_basins - 1) * conc_thick) + 2 * (back_basin_length + 2 * conc_thick / 2)  # pyunits.ft
        max_back_tank_size = 282294  # * pyunits.gallons # maximum backwash tank size - NEED TO DETERMINE DYNAMICALLY
        num_back_tanks = total_backwash * back_multiplier / max_back_tank_size  # Number of backwash tanks

        back_tank_vol = total_backwash * back_multiplier / num_back_tanks  # * pyunits.gallons # Backwash tank volume

        ############## REGENERATION ##############
        regen_list = ['onsite', 'offsite', 'throw_nonhaz', 'offsite_haz', 'throw_haz', 'throw_rad', 'throw_hazrad']
        flow_regen = average_flow_rate * 3.785  # * pyunits.L / pyunits.min # flow rate for Freundlich calculation
        n0e = self.freund1 * gac_density * 453.59 / 0.02832  # * pyunits.mg / pyunits.m ** 3 # for BDST calculation

        if system_type == 'pressure':
            mass_regen = (self.gac_each * num_treat_lines) * 453.59  # * pyunits.gram # mass of GAC for Freundlich calculation
            velocity_regen = flow_regen * 0.001 / (self.max_sa * num_treat_lines * 0.093)  # m / min # for BDST calculation
            bed_depth_regen = bed_depth * 0.3048  # * pyunits.m
            # __ Calculates bed life based on Freundlich isotherm
            self.bed_life = (mass_regen * (self.freund1 / 1000) * (self.conc_in * 1000) ** self.freund2 / (flow_regen * (self.conc_in - self.conc_breakthru))) / (30 * 24 * 60)  # * pyunits.months #
            #         self.bed_life = self.freund1
            #         self.bed_life = (n0e / (1000 * velocity_regen * self.conc_in) * bed_depth_regen - np.log(self.conc_in / self.conc_breakthru - 1) / (self.freund2 * self.conc_in)) / (30*24*60)
            self.avg_regen_rate = self.gac_each * self.op_num_tanks / (self.bed_life / 12) / 365  # * pyunits.lb / pyunits.day

        if system_type == 'gravity':
            mass_regen = self.gac_total * 453.49  # * pyunits.gram # mass of GAC for Freundlich calculation
            velocity_regen = flow_regen * 0.001 / (self.basin_width * self.basin_length * self.tot_num_basins * 0.093)  # m / min # for BDST calculation
            bed_depth_regen = basin_op_depth * 0.3048  # * pyunits.m
            # __ Calculates bed life based on Freundlich isotherm
            self.bed_life = (mass_regen * (self.freund1 / 1000) * (self.conc_in * 1000) ** self.freund2 / (flow_regen * (self.conc_in - self.conc_breakthru))) / (30 * 24 * 60)  # * pyunits.months #
            self.avg_regen_rate = self.gac_each * self.op_num_basins / (self.bed_life / 12) / 365  # * pyunits.lb / pyunits.day

        self.gac_annual = self.avg_regen_rate * 365  # *pyunits.lb / pyunits.year # When regenerating, this quantity is made up of regenerated GAC + makeup GAC

        if regen == 'onsite':
            regen_capacity = (self.avg_regen_rate / regen_runtime) * regen_redund  # * pyunits.lb / pyunits.day # Regeneration capacity needed (on-site only)
            max_furnace_size = 100000  # * pyunits.lb / pyunits.day # maximum furnace size, looked up from table
            num_furnace = regen_capacity / max_furnace_size
            furnace_size = regen_capacity / num_furnace
            regen_annual = (1 - makeup_rate) * self.gac_annual  # * pyunits.lbs / pyunits.year # rate if regenerated on-site
            gac_makeup = makeup_rate * self.gac_annual  # * pyunits.lbs / pyunits.year # makeup rate for onsite regeneration
        if regen == 'offsite':
            regen_annual = (1 - makeup_rate_off) * self.gac_annual  # * pyunits.lbs / pyunits.year # rate if regenerated off-site
            gac_makeup = makeup_rate_off * self.gac_annual  # * pyunits.lbs / pyunits.year # makeup rate for offsite regeneration
        if regen == 'throwaway':
            gac_makeup = self.gac_annual  # * pyunits.lbs / pyunits.year # makeup rate for GAC throwaway

        ############## GAC STORAGE ##############
        # _____ USING THE SAME STORAGE TANK FOR VIRGIN, SPENT, AND/OR REGENERATED GAC _____
        gac_storage_vol = (self.gac_each / gac_density) * virgin_gac_storage  # * pyunits.ft ** 3 # GAC storage on-site only
        storage_basin_depth = (gac_storage_vol / storage_basins) ** (1 / 3) * storage_ratio  # * pyunits.ft # stage basin depth
        storage_basin_width = ((gac_storage_vol / storage_basins) / storage_basin_depth) ** 0.5  # * pyunits.ft
        storage_basin_length = storage_basin_width  # * pyunits.ft
        storage_basin_vol = storage_basin_width * storage_basin_length * storage_basin_depth * 7.48  # * pyunits.gallons
        storage_conc_vol = ((
                                        2 * storage_basin_depth * storage_basin_length + 2 * storage_basin_depth * storage_basin_width + storage_basin_width * storage_basin_length) * 1.2 * conc_thick * storage_basins) / 27  # * pyunits.yard ** 3
        storage_excavation_vol = ((storage_basin_width + overexcavate) * (storage_basin_length + overexcavate) * (storage_basin_depth + overexcavate) + 0.5 * (
                    3 * (storage_basin_depth + overexcavate) * (storage_basin_width + overexcavate) * (storage_basin_depth + overexcavate))) * storage_basins / 27  # * pyunits.yard ** 3
        storage_backfill_vol = storage_excavation_vol - (storage_basin_width * storage_basin_length * storage_basin_depth * storage_basins) / 27  # * pyunits.yard ** 3
        storage_railing = (storage_basin_width * 2 + storage_basin_length * 2) * storage_basins * 2  # * pyunits.ft
        num_storage_tanks = gac_storage_vol * 7.48 / max_back_tank_size
        storage_tank_vol = gac_storage_vol * 7.48 / num_storage_tanks

        ########################################################
        ########################################################
        ############## PUMPS PIPES STRUCTURE ##############
        ########################################################
        ########################################################

        ############## PUMP AND TRANSFER EQUIPMENT  ##############
        transfer_method = 'eductors'
        incl_backwash_pumps = True
        num_redund_eductors = 1

        max_pump_size = 10000  # * pyunits.gallons / pyunits.minute # largest pump size for which costs are available

        pump_rating = (design_flow_rate + bp_flow_rate) * (1 + pump_safety_factor) / num_pumps  # * pyunits.gallons / pyunits.minute # booster pump rating
        num_pumps = None

        if not num_pumps:
            if system_type == 'pressure':
                pump_rating = 0  # pyunits.gallons / pyunits.minute
            elif system_type == 'gravity':
                pump_rating_a = average_flow_rate + bp_flow_rate * average_flow_rate / design_flow_rate
                pump_rating_b = (design_flow_rate + bp_flow_rate) / 2
                pump_rating_c = max(pump_rating_a, pump_rating_b) * (1 + pump_safety_factor)
                pump_rating = min(pump_rating_c, max_pump_size)  # pyunits.gallons / pyunits.minute
        elif num_pumps == 0:
            pump_rating = 0  # pyunits.gallons / pyunits.minute
        elif num_pumps > 0:
            pump_rating = (design_flow_rate + bp_flow_rate) * (1 + pump_safety_factor) / num_pumps  # pyunits.gallons / pyunits.minute
        max_cm_pump_size = 360  # * (pyunits.gallons / pyunits.hour) # The largest size for which costs are available.
        if pump_rating == 0:
            booster_pumps = 0
            total_booster_pumps = 0
        else:
            booster_pumps = (design_flow_rate + bp_flow_rate) * (1 + pump_safety_factor) / pump_rating
            total_booster_pumps = booster_pumps + num_redund_pumps

        back_pump_flow_total = water_flush * (1 + pump_safety_factor)  # * pyunits.gallon / pyunits.minute # backwash pumping flow needed
        if not incl_backwash_pumps:
            num_back_pumps = 0
            back_pump_rating = 0
        else:
            num_back_pumps = back_pump_flow_total / max_pump_size + num_redund_back_pumps
            back_pump_rating = back_pump_flow_total / (num_back_pumps - num_redund_back_pumps)  # * pyunits.gallons / pyunits.minute # backwash pump rating

        if transfer_method == 'eductors':
            transfer_rate = self.gac_each / transfer_time
            max_eductor_size = 54 * gac_density / 7.48 * 60  # * (pyunits.lbs / pyunits.hour) # The largest size for which costs are available. Assumption used only if tanks are used.
            eductors = (transfer_rate / max_eductor_size) + num_redund_eductors

            # The regression for eductors is a linear regression made by fitting the following data to a linear trendline in Excel.
            # Taken from 'Lookup Tables' sheet in the EPA GAC model 'wbs-gac-020818.xls'
            #
            # x = [0, 1673.459893, 3153.406417, 5343.245989, 7942.176471, 9434.15508, 12875.33155] # Transfer Rate (lbs/hr)
            # y = [1.5, 2, 2.5, 3, 4, 6, 8] # Diameter (inch)
            #
            # y = m * x + b
            # diameter = 0.0005 * transfer_rate + 0.9764
            # R_squared = 0.9381

            eductor_size = 0.0005 * transfer_rate + 0.9764  # * pyunits.inches # eductor size NEED TO LOOK UP IN eductor_size_table but don't know where that is

        ########################################################
        ########################################################
        ############## RESIDUALS MANAGEMENT ##############
        ########################################################
        ########################################################

        # discharge = ['surface_water', 'potw', 'recycle', 'septic', 'evaporation_pond']
        discharge = 'surface_water'
        holding_tank = True
        res_cap_factor = 2  # Holding tank/basin capacity safety factor
        dredging_freq = 1  # * pyunits.year * -1 # Evaporation pond solids removal frequency -- Range from 1 to 3 yrs, depending on the final solid concentration required and local climate (Dewatering Municipal Wastewater Sludge,EPA design Manual, Dewatering Municipal Wastewater Sludges.EPA/625/1-87/014, September 1987)
        potw_tss_limit = 250  # * (pyunits.mg / pyunits.liter) # POTW TSS discharge limit (over which fee would be imposed) -- Most common limit for cities with a limit

        ############## SPENT BACKWASH ##############
        res_vol = total_backwash  # * pyunits.gallons # Single event volume -- backwashing one vessel

        if system_type == 'pressure':
            res_stagger_time = backwash_interval * 60 / self.tot_num_tanks  # * pyunits.minute # Time between events
            res_flow_annual = res_vol * self.tot_num_tanks * (365 * 24 / backwash_interval)  # * pyunits.gallons # annual residuals discharge
        elif system_type == 'gravity':
            res_stagger_time = backwash_interval * 60 / self.tot_num_basins  # * pyunits.minute # Time between events
            res_flow_annual = res_vol * self.tot_num_basins * (365 * 24 / backwash_interval)  # * pyunits.gallons # annual residuals discharge

        if holding_tank or discharge == 'recycle':
            res_flow_actual = res_vol / res_stagger_time  # * (pyunits.gallons / pyunits.minute) # Actual residuals discharge flow rate -- Accounts for flow equalization if holding tanks used
            res_flow = res_cap_factor * res_vol / res_stagger_time
        else:
            res_flow_actual = res_vol / backwash_time  # * (pyunits.gallons / pyunits.minute) # Actual residuals discharge flow rate -- Accounts for flow equalization if holding tanks used
            res_flow = res_flow_actual

        ############## EVAPORATION POND OR HOLDING/SEPTIC TANK SOLIDS ##############
        if discharge in ['septic', 'evaporation_pond']:
            tss_in = pyunits.convert(self.conc_mass_in[time, 'tss'], to_units=(pyunits.mg / pyunits.liter))
            tss_out = pyunits.convert(self.conc_mass_out[time, 'tss'], to_units=(pyunits.mg / pyunits.liter))
            if system_type == 'pressure':
                tss_residuals = (tss_in - tss_out) * average_flow * 1E6 * (backwash_interval / 24) / (res_vol * self.tot_num_tanks)  # * (pyunits.mg / pyunits.liter) # TSS in residuals
            elif system_type == 'gravity':
                tss_residuals = (tss_in - tss_out) * average_flow * 1E6 * (backwash_interval / 24) / (res_vol * self.tot_num_basins)  # * (pyunits.mg / pyunits.liter) # TSS in residuals
            if discharge == 'evaporation_pond':
                ep_solids = tss_residuals * res_flow_annual * 3.785 / 1000 / 453.59 / dredging_freq  # * pyunits.lbs # Evaporation pond TSS accumulation

        ############## SPENT MEDIA ##############
        disp_freq = 12 / self.bed_life  # times per year, replacement/disposal frequency
        spent_media = self.gac_total / 2000  # * pyunits.tons # Spent media quantity (total per event)
        spent_media_yr = spent_media * disp_freq  # * pyunits.tons # Spent media quantity (average per year)

        ############## ::: CAPITAL ITEMS ::: ##############

        ############## HOLDING TANKS (FOR FLOW EQUALIZATION) ##############
        max_htank_size = 282094  # * pyunits.gallons # Maximum holding tank size -- The largest size for which costs are available.
        # htanks = # number of holding tanks
        # htank_vol = # * pyunits.gallons # Holding tank volume

        ############## HOLDING BASINS (FOR FLOW EQUALIZATION) ##############

        # holding_ratio = 0.6  # Holding basin depth to volume ratio --
        # holding_freeboard = 3 # * pyunits.ft # holding basin freeboard
        # hmix_hp_per = 0.25 # * (pyunits.hp / (1000 * pyunits.gallons)) # Holding tank/basin mixer horsepower (if coagulant is used)

        # hbasin_redund = # number redundant holding basins
        # hbasins = # number holding basins
        # total_hvol_ft = res_cap_factor * res_vol * hbasin_redund / 7.48 # * pyunits.ft ** 3 # Total residuals storage volume in cubic feet
        # hvol_ft = total_hvol_ft / hbasins # * pyunits.ft ** 3 # Total residuals storage volume in cubic feet
        # hbasin_op_depth = hvol_ft ** (1 / 3) * holding_ratio # * pyunits.ft ** 3 # holding basin operating depth
        # hbasin_width = (hvol_ft / hbasin_op_depth) ** 0.5 # * pyunits.ft # Holding basin width  ## NEEDS TO BE ROUNDED
        # hbasin_length = hbasin_width # * pyunits.ft # Holding basin length
        # hbasin_depth = hbasin_op_depth + holding_freeboard # * pyunits.ft # Holding basin depth including freeboard
        # hbasin_vol = hbasin_width * hbasin_length * hbasin_depth * 7.48 # * pyunits.ft # Holding basin volume  ## NEEDS TO BE ROUNDED
        # hconc_vol = (2 * (hbasin_width * hbasins + conc_thick * (hbasins + 1)) * hbasin_depth * conc_thick + (hbasins + 1) * hbasin_length * hbasin_depth * conc_thick + (
        #             hbasin_length + 2 * conc_thick) * (hbasin_width * hbasins + conc_thick * (hbasins + 1)) * conc_thick) / 27 # * pyunits.yard ** 3 # Concrete volume
        # hexcavation_vol = ((hbasins * hbasin_width + (hbasins + 1) * conc_thick + overexcavate) * (hbasin_length + 2 * conc_thick + overexcavate) * (hbasin_depth + conc_thick + overexcavate) + 0.5 * (
        #             3 * (hbasin_depth + conc_thick + overexcavate) * (hbasin_depth + conc_thick + overexcavate) * (hbasin_length + 2 * conc_thick + overexcavate))) / 27 # * pyunits.yard ** 3 # Excavation volume
        # hbackfill_vol = hexcavation_vol - (hbasins * hbasin_width + (hbasins + 1) * conc_thick) * (hbasin_length + 2 * conc_thick) * (hbasin_depth + conc_thick) / 27 # * pyunits.yard ** 3 # Backfill volume
        # hrailing = 2 * (hbasins * hbasin_width + 2 * conc_thick / 2 + (hbasins - 1) * conc_thick) + 2 * (hbasin_length + 2 * conc_thick / 2) # * pyunits.ft # Railing length



        ############## FERRIC CHLORIDE ADDITION ##############

        ############## POLYMER ADDITION ##############

        ############## SOLIDS TRANSFER FOR HOLDING TANKS ##############
        # res_transfer_rate = res_solids * 2000 / htransfer_time # * (pyunits.lbs / pyunits.hr) # transfer rate required
        # res_transfer_rate_gal = res_transfer_rate / (ht_solids_density / 7.48 * 60) # * (pyunits.gallons / pyunits.minute) # transfer rate in gpm
        # res_slurry_pumps = 1 # number of slurry pump systems
        # res_eductors = res_transfer_rate_gal / max_eductor_size # number of eductors
        # res_eff_transfer_rate = res_transfer_rate_gal / res_eductors # * (pyunits.gallons / pyunits.minute) # Effective transfer rate
        # res_eductor_size =



        ############## SOLIDS DRYING PAD ##############
        # solids_pad_area =
        # solids_pad_concrete =

        ############## SEPTIC SYSTEM ##############
        # max_sept_tank_vol =
        # num_sept_tanks =
        # sept_tank_vol =
        # sept_design_flow =
        # sept_infil_area =
        # sept_trench_bot_area =
        # sept_trenches =
        # sept_trench_I =
        # sept_gravel_vol =
        # sept_trench_excav_vol =
        # sept_tank_side =
        # sept_tank_excav_vol =
        # sept_dist_boxes =
        # sept_pipe_length =
        # sept_fp =

        ############## EVAPORATION POND ##############
        # ep_total_sa =
        # ep_solids_depth =
        # ep_water_depth =
        # ep_depth =
        # ep_cells =
        # ep_cell_side =
        # ep_excavation_vol =
        # ep_backfill_vol =
        # dike_volume =
        # liner_area =


        ############## ::: O & M ITEMS ::: ##############

        ############## PUMPS ##############

        ############## COAGULANT USE ##############

        ############## COAGULANT PURCHASING ##############

        ############## POLYMER PURCHASING ##############

        ############## POTW DISCHARGE FEES ##############
        tss_residuals_dis = tss_residuals  # THERE IS MORE TO DETERMINING THIS VARIABLE BUT NOT SURE IF IT APPLIES
        tss_test = ((tss_residuals_dis - potw_tss_limit) * res_flow_annual * 3.785 / 1000 / 453.59)
        if tss_test > 0:
            ex_tss_total = tss_test  # * (pyunits.lbs / pyunits.year) # Total TSS in excess of POTW limit (if applicable)
        else:
            ex_tss_total = 0  # * (pyunits.lbs / pyunits.year) # Total TSS in excess of POTW limit (if applicable)
        # POTW_base_cost_avg_cl = 15.33 $/month
        # POTW_base_cost_typ_cl = 17.25 $/month
        # POTW_TSS_cost_avg_cl = 0.24 $/lb over limit
        # POTW_TSS_cost_typ_cl = 0.41 $/lb over limit
        # POTW_vol_cost_avg_cl = 4.33 $/ 1000 gallons
        # POTW_vol_cost_typ_cl = 4.46 $/ 1000 gallons

        potw_base = 17.25 * 12  # Annual POTW base fee $ / year
        potw_vol = 0.41 * res_flow_annual / 1000  # Annnual POTW volume fee $ / year
        potw_tss = 4.46 * ex_tss_total  # Annual POTW TSS fee $ / year
        potw_fee = potw_base + potw_vol + potw_tss  # Total Annual POTW discharge fee $ / year

        ############## SPENT MEDIA DISPOSAL FEES ##############
        # Constants from cost lookup tables and inputs from input sheet or design assumptions
        max_waste_ship = 18  # * pyunits.tons # Maximum waste shipment size
        non_haz_miles = 10  # * pyunits.miles # Miles to non-hazardous solid waste disposal site
        haz_miles = 200  # * pyunits.miles # Miles to hazardous solid waste disposal site
        rad_miles = 700  # * pyunits.miles # Miles to radioactive non-hazardous solid waste disposal site
        hazrad_miles = 700  # * pyunits.miles # Miles to radioactive hazardous solid waste disposal site

        nonhaz_disposal_cost = 68.20  # $/ton Non-hazardous waste disposal
        nonhaz_transportation_cost = 0.51  # $/ton*mile Non-hazardous waste transportation
        haz_disposal_cost = 357.60  # $/ton Hazardous waste disposal
        haz_trans_min_cost = 3067.09  # $/shipment Hazardous waste minimum charge per shipment
        haz_transportation_cost = 0.11  # $/ton*mile Hazardous waste transportation
        hazrad_annual_fee = 1585.06  # $/year Radioactive hazardous waste annual fee
        hazrad_disposal_cost = 11043.39  # $/ton Radiactive hazardous waste disposal
        hazrad_trans_min_cost = haz_trans_min_cost
        hazrad_transportation_cost = 0.26  # $/ton*mile radiactive hazardous waste transportation
        rad_annual_fee = hazrad_annual_fee  # $/year radiactive waste annual fee
        rad_disposal_cost = 5145.16  # $/ton radiactive waste disposal
        rad_transportation_cost = hazrad_transportation_cost  # $/ton*mile radioactive waste transportation
        rad_trans_min_cost = hazrad_trans_min_cost

        regen_list = ['onsite', 'offsite', 'throw_nonhaz', 'offsite_haz', 'throw_haz', 'throw_rad', 'throw_hazrad']

        # 1 for regeneration onsite, 2 for regeneration off-site (non-hazardous), 3 for throwaway (non-hazardous), 4 for regeneration off-site (hazardous), 5 for throwaway (hazardous),
        # 6 for throwaway (radioactive), 7 for throwaway (hazardous & radioactive)
        if spent_media > max_waste_ship:
            disposal_shipments = spent_media / max_waste_ship * disp_freq  # Shipments per year ##  NEEDS TO BE ROUNDED UP SOMEHOW
        else:
            disposal_shipments = disp_freq

        if regen in ['onsite', 'offsite', 'offsite_haz']:
            disposal = 0  # $/year -- cost for disposal
            transport_unit = 0  # $/ton*mile -- transportation unit cost
            transport_min = 0  # $/shipment -- transportation minimum charge per shipment
            disposal_miles = 0  # miles -- transportation mileage
        if regen == 'throw_nonhaz':
            disposal = spent_media * disp_freq * nonhaz_disposal_cost  # $/year -- cost for disposal
            transport_unit = nonhaz_transportation_cost  # $/ton*mile -- transportation unit cost
            transport_min = 0  # $/shipment -- transportation minimum charge per shipment
            disposal_miles = non_haz_miles  # miles -- transportation mileage
        if regen == 'throw_haz':
            disposal = spent_media * disp_freq * haz_disposal_cost  # $/year -- cost for disposal
            transport_unit = haz_transportation_cost  # $/ton*mile -- transportation unit cost
            transport_min = haz_trans_min_cost  # $/shipment -- transportation minimum charge per shipment
            disposal_miles = haz_miles  # miles -- transportation mileage
        if regen == 'throw_rad':
            disposal = spent_media * disp_freq * rad_disposal_cost  # $/year -- cost for disposal
            transport_unit = rad_transportation_cost  # $/ton*mile -- transportation unit cost
            transport_min = rad_trans_min_cost  # $/shipment -- transportation minimum charge per shipment
            disposal_miles = rad_miles  # miles -- transportation mileage
        if regen == 'throw_hazrad':
            disposal = spent_media * disp_freq * hazrad_disposal_cost  # $/year -- cost for disposal
            transport_unit = hazrad_transportation_cost  # $/ton*mile -- transportation unit cost
            transport_min = hazrad_trans_min_cost  # $/shipment -- transportation minimum charge per shipment
            disposal_miles = hazrad_miles  # miles -- transportation mileage

        transportation = max(disposal_shipments * transport_min, spent_media * disp_freq * disposal_miles * transport_unit)  # $ maximum transportation fee

        if regen in ['onsite', 'offsite', 'throw_nonhaz', 'offsite_haz', 'throw_haz']:
            disposal_fee = disposal + transportation  # $/year -- total annual spent media disposal fee
        else:
            disposal_fee = disposal + transportation + hazrad_annual_fee  # $/year -- total annual spent media disposal fee



        ########################################################
        ########################################################
        ############## O & M ##############
        ########################################################
        ########################################################



        ############## ENERGY ##############
        # pump_hp =
        # pump_energy =
        #
        # back_pump_psi =
        # back_pump_hp =
        # back_hrs_yr =
        # back_pump_energy =

        ############## REGEN ENERGY ##############
        # regen_energy =
        # regen_ng =
        #

        pump_head = 44  # * pyunits.ft # pump head for booster pumps, can be adjusted by user input
        back_pump_head = 33  # * pyunits.ft # backwash pump head
        res_pump_psi = 25  # * pyunits.psi # residual pump head
        pump_efficiency = 0.75  # * pyunits.dimensionless # pump efficiency
        if bp_pct > 0:
            pump_hp = average_flow_rate / bp_pct * pump_head * 0.43351482 / booster_pumps / pump_efficiency / 14.7 * 33.9 * 8.34 / 550 / 60

        transfer_rate = self.gac_each / transfer_time  # * pyunits.lb / pyunits.hour # transfer rate required
        max_eductor_size = 12784  # * pyunits.lb / pyunits.hour # maximum eductor size
        num_redund_eductors = 1
        eductors = transfer_rate / max_eductor_size + num_redund_eductors

        # eductor_size = transfer_rate / eductors - num_redund_eductors) ---> look up this size in size table

        # _______________________________________________________  # _______________________________________________________  ############## ACTUALLY CALCULATING COST ##############  # _______________________________________________________  # _______________________________________________________

        # CONTACTORS  ## PRESSURE VESSELS
        def fixed_cap():
            def gac_cost_curves(eqn, x):
                cost_df = pd.read_csv('data/gac_cost_eqns.csv', index_col='eqn')
                cost_df.drop(columns=['pct_deviation', 'date_modified', 'r_squared', 'max_size', 'min_size'], inplace=True)
                coeffs = dict(cost_df.loc[eqn].items())
                cost = coeffs['C1'] * x ** coeffs['C2'] + coeffs['C3'] * log(x) + coeffs['C4'] + coeffs['C5'] * exp(coeffs['C6'] * x) + coeffs['C7'] * x ** 3 + coeffs['C8'] * x ** 2 + coeffs[
                    'C9'] * x + coeffs['C10']
                return cost

            pv_material_list = ['stainless', 'carbon with stainless', 'carbon with plastic', 'fiberglass']

            if system_type == 'pressure':
                #         comm_vol = comm_vol * 7.48  # gal - converting from ft3 to gal
                pv_ss_cost = gac_cost_curves('ss_pv_eq', comm_vol * 7.48)  # cost of stainless steel pressure vessel
                pv_cs_cost = gac_cost_curves('cs_pv_eq', comm_vol * 7.48)  # cost of carbon steel pressure vessels with stainless internals
                pv_csp_cost = gac_cost_curves('csp_pv_eq', comm_vol * 7.48)  # cost of carbon steel pressure vessels with plastic internals
                pv_fg_cost = gac_cost_curves('fg_pv_eq', comm_vol * 7.48)  # cost of fiberglass pressure vessels
                if pv_material == 'stainless':
                    pv_cost = pv_ss_cost * self.tot_num_tanks
                if pv_material == 'carbon with stainless':
                    pv_cost = pv_cs_cost * self.tot_num_tanks
                if pv_material == 'carbon with plastic':
                    pv_cost = pv_csp_cost * self.tot_num_tanks
                if pv_material == 'fiberglass':
                    pv_cost = pv_fg_cost * self.tot_num_tanks

            ## GAC CONTACT BASINS
            if system_type == 'gravity':
                concrete_contact_cost = basin_conc_vol * 582.09  # 'conc_basin_cost_cl' cost per cubic yard of concrete
                first_underdrain_cost = gac_cost_curves('cont_bot_eq', self.basin_area)
                add_underdrain_cost = gac_cost_curves('cont_bot_add_eq', self.basin_area)
                back_dist_cost = gac_cost_curves('cont_top_eq', self.basin_length)
                internals_cost = first_underdrain_cost + (self.tot_num_basins - 1) * add_underdrain_cost + self.tot_num_basins * back_dist_cost
                railing_cost = (railing * 36)  # 'metal_cost_cl' cost per linear foot
                stairs_cost = (num_stairs * 541.43)  # 'metal_cost_cl' cost per riser
                excavation_cost = (excavation_vol * 30.08)  # 'excavate_cost_cl' cost per cubic yard of excavation
                backfill_compact_cost = (backfill_vol * 13.95)  # 'backfill_cost_cl' cost per cubic yard of backfill

                basin_cost = concrete_contact_cost + internals_cost + railing_cost + stairs_cost + excavation_cost + backfill_compact_cost

            # TANKS
            ## BACKWASH BASINS/TANKS

            #     bw_tank_type_list = ['concrete', 'stainless', 'fiberglass', 'hdpe']
            #     bw_tank_type = 'stainless'

            concrete_back_cost = num_back_basins * (back_conc_vol * 582.09 + back_excavation_vol * 30.08 + back_backfill_vol * 13.95 + back_railing * 36)
            bw_ss_cost = gac_cost_curves('st_bwt_eq', back_tank_vol)
            bw_fg_cost = gac_cost_curves('fg_bwt_eq', back_tank_vol)
            bw_hdpe_cost = gac_cost_curves('hdpe_bwt_eq', back_tank_vol)

            if bw_tank_type == 'concrete':
                bw_tank_cost = concrete_back_cost * num_back_basins
            if bw_tank_type == 'stainless':
                bw_tank_cost = bw_ss_cost * num_back_tanks
            if bw_tank_type == 'fiberglass':
                bw_tank_cost = bw_fg_cost * num_back_tanks
            if bw_tank_type == 'hdpe':
                bw_tank_cost = bw_hdpe_cost * num_back_tanks

            ## HOLDING TANKS
            # ht_ss_cost = gac_cost_curves('st_bwt_eq', back_tank_vol)
            # ht_fb_cost = gac_cost_curves('fg_bwt_eq', back_tank_vol)
            # ht_hdpe_cost =

            # PUMPS
            booster_pump_cost = gac_cost_curves('pump_eq', pump_rating)
            bw_pump_cost = gac_cost_curves('back_pump_eq', back_pump_rating)
            # res_pump_cost = gac_cost_curves('pump_eq', res_pump_rating)

            #  MEDIA AND CHEMICALS
            ## INITIAL GAC CHARGE
            gac_cost = gac_cost_curves('gac_eq', self.gac_total)
            # fecl3_cost =

            # ONSITE GAC REGENERATION
            ## MULTIPLE HEARTH FURNACE SYSTEM
            # furnace_cost = gac_cost_curves('on_regen_eq', furnace_size)

            ## STORAGE
            storage_ss_cost = gac_cost_curves('st_bwt_eq', storage_tank_vol) * 3  # multiplied by 3 to account for virigin, spent, and regen GAC storage
            # storage_conc_cost =

            ##### TOTAL SYSTEM COST #####
            if system_type == 'pressure':
                total_system_cost = pv_cost + bw_tank_cost + booster_pump_cost + bw_pump_cost + gac_cost + storage_ss_cost

            if system_type == 'gravity':
                total_system_cost = basin_cost + bw_tank_cost + booster_pump_cost + bw_pump_cost + gac_cost + storage_ss_cost

            return total_system_cost * 1E-6

        def autosize(system_type, flow, num_tanks, num_lines, ebct, ebct_tank, geom='vertical'):

            def autosize_constraints(system_type, flow=flow, num_tanks=num_tanks, num_lines=num_lines, ebct=ebct, geom=geom):

                if system_type == 'pressure':
                    # vessel surface area
                    comp_min_sa_vessel = comp_sa_min / num_lines  # based on max load, design flow, and target number of lines
                    comp_max_sa_vessel = comp_sa_max / num_lines  # based on min load, design flow, and target number of lines

                    if geom == 'vertical':
                        # vertical vessel height
                        comp_min_vert_height = 3  # from reasonable dimensions table
                        comp_max_vert_height = 14  # from reasonable dimensions table

                        # vertical bed depth
                        min_depth_a = comp_vol_required / num_tanks / sa_all_vessels  # ensures that bed depth is sufficient to pass diameter check on vessel design sheet
                        min_depth_b = min_bed_depth  # from guidance on input sheet
                        comp_min_vert_bed_depth = max(min_depth_a, min_depth_b)  # strictest of the above
                        max_depth_a = (max_height - freeboard) / (1 + bed_expansion)  # max bed depth for max_height, given freeboard and bed expansion
                        max_depth_b = max_bed_depth  # from guidance on input sheet
                        comp_max_vert_bed_depth = min(max_depth_a, max_depth_b)  # strictest max of the above, rounded

                        # vertical vessel diameter
                        min_diam_a = 2 * ((
                                                      comp_vol_required / num_tanks / 3.14159 / comp_max_vert_bed_depth / num_lines) ** 0.5 + vessel_thickness)  # min diam to avoid bed depth becoming too deep, given required volume
                        min_diam_b = 2 * ((comp_min_sa_vessel / 3.14159) ** 0.5 + vessel_thickness)  # from min surface area
                        min_diam_c = 1.5  # from reasonable dimensions table
                        comp_min_vert_diam = 2 * max(min_diam_a, min_diam_b, min_diam_c), 0 / 2
                        max_diam_a = 14  # max diameter CDA
                        max_diam_b = 2 * ((comp_max_sa_vessel / 3.14159) ** 0.5 + vessel_thickness)  # from max surface area
                        comp_max_vert_diam = max(0.5, 2 * min(max_diam_a, max_diam_b) / 2)  # from reasonable dimensions table

                        return comp_min_vert_height, comp_max_vert_height, comp_min_vert_diam, comp_max_vert_diam, comp_min_vert_bed_depth, comp_max_vert_bed_depth

                    if geom == 'horizontal':
                        # horizontal vessel diameter
                        comp_min_horiz_diam = 8  # from guidance provided by Bob Dvorin, 5/16/05
                        comp_max_horiz_diam = min(max_height, max_diam)  # strictest of max_height CDA and max_diam CDA

                        # horizontal vessel length
                        min_length_a = comp_min_sa_vessel / (comp_horiz_diam - 2 * vessel_thickness)  # from max load and actual diameter
                        min_length_b = 20
                        comp_min_horiz_length = max(min_length_a, min_length_b)
                        max_length_a = max_length  # max length CDA
                        max_length_b = comp_max_vol / (comp_horiz_diam * comp_horiz_diam * 3.14159 / 4) / 7.48  # max volume combined with actual diameter
                        comp_max_horiz_length = min(max_length_a, max_length_b)

                        # horizontal bed depth
                        min_depth_a = comp_vol_required / num_tanks / sa_all_vessels  # ensures that bed depth is sufficient for required volume of medium
                        min_depth_b = min_bed_depth  # from media constraint table
                        comp_min_horiz_bed_depth = max(min_depth_a, min_depth_b)
                        max_depth_a = (min(max_height, max_diam) - freeboard) / (1 + bed_expansion)  # max bed depth for max_height or max_diam, given freeboard and bed expansion
                        max_depth_b = max_bed_depth  # from media constraint table
                        comp_max_horiz_bed_depth = min(max_depth_a, max_depth_b)

                        return comp_min_horiz_diam, comp_max_horiz_diam, comp_min_horiz_length, comp_max_horiz_length, comp_min_horiz_bed_depth, comp_max_horiz_bed_depth

                if system_type == 'gravity':
                    # bed depth
                    min_depth_a = min_depth  # from min_depth CDA
                    min_depth_b = flow * ebct / (num_lines * 30 * max_width) / 7.48  # assuming max-size contactor and number of contactors above, min depth for sufficient media volume
                    comp_min_bed_depth_a = max(min_depth_a, min_depth_b)
                    comp_max_bed_depth_a = max_depth  # from max_depth CDA

                    # surface area
                    comp_min_sa_a = flow / num_lines / load_max  # from loading: based on design flow per target line, max loading
                    comp_max_sa_a = flow / num_lines / load_min  # from loading: based on design flow per target line, min loading

                    # contactor length
                    comp_min_length_a = 6  # from min_length CDA
                    comp_max_length_a = 30  # from max_length CDA

                    # contactor width
                    comp_min_width_a = min_width  # from min_width CDA
                    comp_max_width_a = max_width  # from max_width CDA

                    return comp_min_bed_depth_a, comp_max_bed_depth_a, comp_min_sa_a, comp_max_sa_a, comp_min_length_a, comp_max_length_a, comp_min_width_a, comp_max_width_a

                ## PRESSURE ##

            if system_type == 'pressure':

                comp_vol_required_stg1 = flow * ebct_tank / 7.48  # volume of media in first-stage vessels
                comp_sa_min = flow / load_max  # to reach maximum loading rate
                comp_sa_max = flow / load_min  # to reach minimum loading rate
                comp_vol_required = flow * ebct / 7.481  # volume of media in all vessels

                if geom == 'vertical':
                    comp_target_bed_depth_vert = target_bed_depth_over  # based on target load CDA
                    comp_sa_required_vert = comp_vol_required_stg1 / comp_target_bed_depth_vert  # based on media volume and bed depth
                    comp_vert_diam = 2 * ((comp_sa_required_vert / num_lines / 3.14159) ** 0.5 + vessel_thickness)  # target diameter
                    sa_one_vessel = (comp_vert_diam - 2 * vessel_thickness) * (comp_vert_diam - 2 * vessel_thickness) * 3.14159 / 4  # surface area, one vessel
                    sa_all_vessels = sa_one_vessel * num_lines  # surface area, all vessels

                    comp_min_vert_height, comp_max_vert_height, comp_min_vert_diam, comp_max_vert_diam, comp_min_vert_bed_depth, comp_max_vert_bed_depth = autosize_constraints(system_type, geom=geom)

                    # vertical design search
                    comp_vert_max_media = (comp_max_vert_diam / 2 - vessel_thickness) * (
                            comp_max_vert_diam / 2 - vessel_thickness) * 3.14159 * comp_max_vert_bed_depth  # based on guidance and CDAs for max dimensions
                    comp_vert_max_sa = (max_diam / 2 - vessel_thickness) * (max_diam / 2 - vessel_thickness) * 3.14159  # based on max_diam CDA

                    num_lines_vert_a = comp_sa_min / comp_vert_max_sa  # based on surface area from max load
                    num_lines_vert_b = comp_sa_required_vert / comp_vert_max_sa  # based on surface area from bed depth
                    num_lines_vert_c = comp_vol_required_stg1 / comp_vert_max_media  # based on media volume
                    comp_vert_min_number = max(num_lines_vert_a, num_lines_vert_b, num_lines_vert_c)

                    # inputs

                    comp_vert_bed_depth = comp_vol_required / num_tanks / sa_all_vessels  # bed depth
                    comp_vert_height = (1 + bed_expansion) * comp_vert_bed_depth + freeboard  # target height
                    comp_bed_depth = comp_vert_bed_depth  # bed depth for chosen geometry

                    if comp_vert_diam < comp_min_vert_diam:
                        comp_vert_diam = comp_min_vert_diam
                    elif comp_vert_diam > comp_max_vert_diam:
                        comp_vert_diam = comp_max_vert_diam
                    else:
                        comp_vert_diam = 2 * comp_vert_diam / 2

                    if comp_min_vert_bed_depth <= comp_max_vert_bed_depth:
                        if comp_bed_depth < comp_min_vert_bed_depth:
                            comp_bed_depth = comp_min_vert_bed_depth
                        elif comp_bed_depth > comp_max_vert_bed_depth:
                            comp_bed_depth = comp_max_vert_bed_depth
                        else:
                            comp_bed_depth = comp_vert_bed_depth

                    if comp_min_vert_height > comp_max_vert_height:
                        comp_vert_height = -1
                        print(f'Min vert height greater than max vert height.\n\tcomp_min_vert_height = {comp_min_vert_height}\n\tcomp_max_vert_height = {comp_max_vert_height}')
                        print('I am not sure what this means yet.')
                    elif comp_vert_height > comp_max_vert_height:
                        comp_vert_height = comp_max_vert_height
                    elif comp_vert_height < comp_min_vert_height:
                        comp_vert_height = 2 * comp_vert_height / 2  ## NEED TO HAVE A ROUNDUP FUNCTION HERE

                    return comp_vert_min_number, comp_vert_height, comp_bed_depth, comp_vert_diam

                if geom == 'horizontal':

                    comp_min_horiz_diam, comp_max_horiz_diam, comp_min_horiz_length, comp_max_horiz_length, comp_min_horiz_bed_depth, comp_max_horiz_bed_depth = autosize_constraints(system_type,
                                                                                                                                                                                      geom=geom)
                    # inputs
                    comp_max_vol = 27100  # max pressure vessel volume LOOKED UP
                    comp_max_vol_length = comp_max_vol / 7.48 / (3.14159 * comp_max_horiz_diam * comp_max_horiz_diam / 4)  # rounded to reflect the length we will actually use on the input sheet
                    comp_target_bed_depth_horiz = target_bed_depth_horiz  # based on target load CDA
                    comp_sa_required_horiz = comp_vol_required_stg1 / comp_target_bed_depth_horiz  # based on media volume and bed depth

                    fb = comp_max_vol_length * (comp_max_horiz_diam * comp_max_horiz_diam / 2 * np.arcsin((freeboard / comp_max_horiz_diam) ** 0.5) - (comp_max_horiz_diam / 2 - freeboard) * (
                            (comp_max_horiz_diam - freeboard) * freeboard) ** 0.5)  # freeboard - volume of a horizontal slice of a cylinder
                    ud = comp_max_vol_length * (
                            comp_max_horiz_diam * comp_max_horiz_diam / 2 * np.arcsin((horiz_underdrain / comp_max_horiz_diam) ** 0.5) - (comp_max_horiz_diam / 2 - horiz_underdrain) * (
                            (comp_max_horiz_diam - horiz_underdrain) * horiz_underdrain) ** 0.5)  # underdrain
                    comp_horiz_void_required = fb + ud  # total of the two void volumes above
                    comp_horiz_void_area = comp_horiz_void_required / comp_max_vol_length  # assumed void volume per length
                    comp_horiz_expanded_bd = comp_target_bed_depth_horiz * (1 + bed_expansion)  # target bed depth after expansion
                    comp_horiz_diam = (comp_horiz_expanded_bd + (comp_horiz_expanded_bd * comp_horiz_expanded_bd + 3.14159 * comp_horiz_void_area) ** 0.5) / (3.14159 / 2)  # target diameter
                    # comp_horiz_diam_old = (comp_sa_required_horiz / num_lines / length_diam_ratio) ** 0.5
                    comp_horiz_length = comp_sa_required_horiz / (comp_horiz_diam - 2 * vessel_thickness) / num_lines  # target length
                    sa_all_vessels = num_lines * (comp_horiz_diam - 2 * vessel_thickness) * comp_horiz_length  # surface area for all vessels
                    comp_horiz_bed_depth = comp_vol_required / num_tanks / sa_all_vessels
                    comp_bed_depth = comp_horiz_bed_depth  # bed depth for chosen geometry

                    # horizontal design search

                    comp_max_horiz_sa = (comp_max_horiz_diam - 2 * vessel_thickness) * comp_max_vol_length  # max vessel surface area
                    comp_target_bed_depth_horiz = target_bed_depth_horiz  # based on target load CDA -- NEEDS TO BE ADJUSTABLE FOR FLOW AND INCLUSION OF UV AOP
                    comp_sa_required_horiz = comp_vol_required_stg1 / comp_target_bed_depth_horiz  # total vessel surface area, based upon media volume and ved depth

                    comp_horiz_max_media = (comp_max_vol / 7.481 - comp_horiz_void_required) / (1 + bed_expansion)  # max media volume
                    num_lines_horiz_a = comp_sa_min / comp_max_horiz_sa  # based on surface area from max load
                    num_lines_horiz_b = comp_sa_required_horiz / comp_max_horiz_sa  # based on surface area from bed depth
                    num_lines_horiz_c = comp_vol_required_stg1 / comp_horiz_max_media  # based on media volume
                    comp_horiz_min_number = max(num_lines_horiz_a, num_lines_horiz_b, num_lines_horiz_c)  # min number of lines, horizontal vessels

                    if comp_min_horiz_diam <= comp_max_horiz_diam:
                        if comp_horiz_diam < comp_min_horiz_diam:
                            comp_horiz_diam = comp_min_horiz_diam
                        elif comp_horiz_diam > comp_max_horiz_diam:
                            comp_horiz_diam = comp_max_horiz_diam
                        else:
                            comp_horiz_diam = 2 * comp_horiz_diam / 2  ##  NEED ROUND UP FUNCtiON HERE

                    if comp_min_horiz_length <= comp_max_horiz_length:
                        if comp_horiz_length < comp_min_horiz_length:
                            comp_horiz_length = comp_min_horiz_length
                        elif comp_horiz_length > comp_max_horiz_length:
                            comp_horiz_length = comp_max_horiz_length
                        else:
                            comp_horiz_length = comp_horiz_length

                    return comp_max_horiz_sa, comp_horiz_length, comp_bed_depth, comp_horiz_min_number

            if system_type == 'gravity':
                comp_min_bed_depth_a, comp_max_bed_depth_a, comp_min_sa_a, comp_max_sa_a, comp_min_length_a, comp_max_length_a, comp_min_width_a, comp_max_width_a = autosize_constraints(system_type,
                                                                                                                                                                                          geom=geom)

                comp_vol_required_a = flow * ebct / 7.481  # volume of media in all vessels
                # design search
                comp_vert_max_media_a = comp_max_bed_depth_a * comp_max_length_a * comp_max_width_a  # based on guidance and CDAs for max dimensions
                comp_sa_min_a = flow / load_max  # to reach maximum loading rate
                comp_sa_max_a = flow / load_min  # to reach minimum loading rate
                comp_target_bed_depth_vert_a = target_bed_depth_over  ## based on Target Bed Depth CDA -- NEEDS TO BE ADJUSTABLE FOR SMALLER FLOWS AND INCLUSION (OR NOT) OF UV AOP... SEE DOCUMENTATION AND EXCEL SHEET
                comp_sa_required_vert_a = comp_vol_required_a / comp_target_bed_depth_vert_a  # based on media volume and bed depth
                num_lines_grav_a = comp_min_sa_a / comp_sa_max_a
                num_lines_grav_b = comp_sa_required_vert_a / comp_sa_max_a
                num_lines_grav_c = comp_vol_required_a / comp_vert_max_media_a
                comp_vert_min_number_a = min(num_lines_grav_a, num_lines_grav_b, num_lines_grav_c)  # below this number of lines, we are constrained to horizontal vessels

                comp_length_width_a = (comp_sa_required_vert_a / num_lines) ** 0.5  # target side length
                sa_one_vessel = comp_length_width_a ** 2  # surface area one vessel
                sa_all_vessels = num_lines * sa_one_vessel  # surface area all vessels
                comp_bed_depth_a = comp_vol_required_a / num_tanks / sa_all_vessels  # bed depth

                if comp_length_width_a < comp_min_length_a:
                    comp_length_width_a = comp_min_length_a
                elif comp_length_width_a > comp_max_length_a:
                    comp_length_width_a = 2 * comp_length_width_a / 2  ## NEED ROUND UP FUNCTION HERE=

                return comp_length_width_a, comp_bed_depth_a, comp_vert_min_number_a

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
