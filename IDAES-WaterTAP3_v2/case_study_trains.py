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

from split_test2 import Separator1
from mixer_example import Mixer1
import watertap as wt

global case_study
global reference
global water_type

from water_props import WaterParameterBlock

from pyomo.environ import (
    Block, Constraint, Expression, Var, Param, NonNegativeReals, units as pyunits)
from idaes.core.util.exceptions import ConfigurationError

def unit_test_case(unit_name = None, flow = None, m = None):
        
        import generate_constituent_list
        generate_constituent_list.case_study = case_study
        generate_constituent_list.reference = reference
        generate_constituent_list.water_type = water_type
        generate_constituent_list.unit_process_list = [unit_name]
        
        ### FOR CHEMICAL ADDITION MODULES. need list of unit processes in train first, to get the chemical dicts from each UP.
        train_constituent_list = generate_constituent_list.run()
        
        m.fs.water = WaterParameterBlock()
                
        if case_study == "Carlsbad":

            m = wt.design.add_water_source(m = m, source_name = "source1", link_to = None, 
                                 reference = reference, water_type = water_type, 
                                 case_study = case_study,
                                           flow = flow) # m3/s (4.38 m3/s = 16500 m3/h = 104.6121 MGD = 4.5833 m3/s)
        
        m = wt.design.add_unit_process(m = m, unit_process_name = unit_name, unit_process_type = unit_name)
        m.fs.arc1 = Arc(source=m.fs.source1.outlet, destination = getattr(m.fs, unit_name).inlet)
        
        return m
        
def get_case_study(flow = None, m = None):
    
    import generate_constituent_list
    generate_constituent_list.case_study = case_study
    generate_constituent_list.reference = reference
    generate_constituent_list.water_type = water_type
    #generate_constituent_list.unit_process_list = [unit_name]

    ### FOR CHEMICAL ADDITION MODULES. need list of unit processes in train first, to get the chemical dicts from each UP.
    train_constituent_list = generate_constituent_list.run()

    m.fs.water = WaterParameterBlock()
        
    unit_processes = get_unit_processes(case_study = case_study)
                          
        
    m = wt.design.add_water_source(m = m, source_name = "source1", link_to = None, 
                         reference = reference, water_type = water_type, 
                         case_study = case_study,
                                   flow = flow) # m3/s (4.38 m3/s = 16500 m3/h = 104.6121 MGD = 4.5833 m3/s)

    # add all unit models to flowsheet
    for unit_process in unit_processes:
        m = wt.design.add_unit_process(m = m, 
                                       unit_process_name = unit_process, 
                                       unit_process_type = unit_process)

    # add mixer for recycled water (backwash)
    m.fs.mixer1 = Mixer1(default={"property_package": m.fs.water, "inlet_list": ["inlet1", "inlet2"]})

    # connect unit models
    ### NOTE THE ARC METHOD IS PROBABLY EASIER FOR NOW ### (compared to  wt.design.connect_blocks)
    ### TODO AUTOMATE WAY TO CONNECT?!
    
    if case_study == "Carlsbad":
    
        m.fs.arc1 = Arc(source=m.fs.source1.outlet, 
                        destination=m.fs.sw_onshore_intake.inlet)
        m.fs.arc2 = Arc(source=m.fs.sw_onshore_intake.outlet, 
                        destination=m.fs.coag_and_floc.inlet)
        m.fs.arc3 = Arc(source=m.fs.coag_and_floc.outlet, 
                        destination=m.fs.mixer1.inlet1) # for recycle
        m.fs.arc4 = Arc(source=m.fs.mixer1.outlet, 
                        destination=m.fs.tri_media_filtration.inlet) # for recycle
        m.fs.arc5 = Arc(source=m.fs.tri_media_filtration.waste, 
                        destination=m.fs.backwash_solids_handling.inlet) # for recycle
        m.fs.arc6 = Arc(source=m.fs.backwash_solids_handling.outlet, 
                        destination=m.fs.mixer1.inlet2) # for recycle
        m.fs.arc7 = Arc(source=m.fs.tri_media_filtration.outlet, 
                        destination=m.fs.sulfuric_acid_addition.inlet)
        m.fs.arc8 = Arc(source=m.fs.sulfuric_acid_addition.outlet, 
                        destination=m.fs.sodium_bisulfite_addition.inlet)
        m.fs.arc9 = Arc(source=m.fs.sodium_bisulfite_addition.outlet, 
                        destination=m.fs.cartridge_filtration.inlet)
        m.fs.arc10 = Arc(source=m.fs.cartridge_filtration.outlet, 
                         destination=m.fs.ro_deep.inlet)
        m.fs.arc11 = Arc(source=m.fs.ro_deep.outlet, 
                         destination=m.fs.lime_softening.inlet)
        m.fs.arc12 = Arc(source=m.fs.lime_softening.outlet, 
                         destination=m.fs.co2_addition.inlet)
        m.fs.arc13 = Arc(source=m.fs.co2_addition.outlet, 
                         destination=m.fs.chlorination_twb.inlet)
        m.fs.arc14 = Arc(source=m.fs.chlorination_twb.outlet, 
                         destination=m.fs.ammonia_addition.inlet)
        m.fs.arc15 = Arc(source=m.fs.ammonia_addition.outlet, 
                         destination=m.fs.treated_storage_24_hr.inlet)
        m.fs.arc16 = Arc(source=m.fs.treated_storage_24_hr.outlet, 
                         destination=m.fs.municipal_drinking.inlet)

        ################################################    
        #### ADD CONNECTIONS TO SURFAACE DISCHARGE ###
        ################################################    

        i = 0
        waste_inlet_list = []

        for b_unit in m.fs.component_objects(Block, descend_into=False):
            if hasattr(b_unit, 'waste'):

                if len(getattr(b_unit, "waste").arcs()) == 0:
                    print(b_unit)
                    i = i + 1
                    waste_inlet_list.append(("inlet%s" % i))

        i = 0
        j = 16 # automate getting this number and the mixer 2 number below. 
        m.fs.mixer2 = Mixer1(default={"property_package": m.fs.water, "inlet_list": waste_inlet_list})

        for b_unit in m.fs.component_objects(Block, descend_into=False):
             if hasattr(b_unit, 'waste'):

                if len(getattr(b_unit, "waste").arcs()) == 0:
                    print(b_unit)
                    i = i + 1
                    j = j + 1

                    if check_waste(b_unit) == "no":

                        setattr(m.fs, ("arc%s" % j), Arc(source = getattr(b_unit, "waste"),  
                                                           destination = getattr(m.fs.mixer2, "inlet%s" % i)))     


        j = j + 1                
        # add connection for waste mixer to surface dicharge
        setattr(m.fs, ("arc%s" % j), Arc(source = getattr(m.fs.mixer2, "outlet"),  
                                                           destination = getattr(m.fs, "surface_discharge").inlet))


        ################################################    
        #### ADD CONNECTIONS TO LANDFILL WASTE ###
        ################################################  
        if "backwash_solids_handling" in unit_processes:
            j = j + 1                
            # add connections to any landfill and surface dicharge
            setattr(m.fs, ("arc%s" % j), Arc(source = getattr(m.fs.backwash_solids_handling, "waste"),  
                                                               destination = getattr(m.fs, "landfill").inlet))
        

    return m

                          
def get_unit_processes(case_study):
    unit_processes = []
    
    if case_study == "Carlsbad":
    
        unit_processes = ["sw_onshore_intake",
                      "coag_and_floc",
                      "tri_media_filtration",
                      "sulfuric_acid_addition",
                      "sodium_bisulfite_addition",
                      "cartridge_filtration",
                      "ro_deep",                 
                      "lime_softening",                  
                      "co2_addition",                  
                      "chlorination_twb",                  
                      "ammonia_addition",                  
                      "treated_storage_24_hr",
                      "municipal_drinking",
                      "backwash_solids_handling",
                      "surface_discharge",
                      "landfill"]
    
    
    if len(unit_processes) == 0: 
        return print("error: no unit processes listed to build treatment train")
        
    return unit_processes


def check_waste(b_unit):
    check = "no"
    
    if "backwash_solids_handling" in str(b_unit): check = "yes"
    
    if "landfill" in str(b_unit): check = "yes"
    
    if "surface_discharge" in str(b_unit): check = "yes"
    
    if "source1" in str(b_unit): check = "yes"
    
    if "municipal_drinking" in str(b_unit): check = "yes"
    
    return check
                          
                          
                          
                          
