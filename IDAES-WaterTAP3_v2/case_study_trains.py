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
        
def get_case_study(name = None, flow = None, m = None):
    
    import generate_constituent_list
    generate_constituent_list.case_study = case_study
    generate_constituent_list.reference = reference
    generate_constituent_list.water_type = water_type
    generate_constituent_list.unit_process_list = [unit_name]

    ### FOR CHEMICAL ADDITION MODULES. need list of unit processes in train first, to get the chemical dicts from each UP.
    train_constituent_list = generate_constituent_list.run()

    m.fs.water = WaterParameterBlock()
        
        
    if name == 'Carlsbad':
        
        m = wt.design.add_water_source(m = m, source_name = "source1", link_to = None, 
                             reference = "NAWI", water_type = "Seawater", 
                             case_study = "Carlsbad",
                                       flow = flow) # m3/s (4.38 m3/s = 16500 m3/h = 104.6121 MGD = 4.5833 m3/s)

        # add unit models
        m = wt.design.add_unit_process(m = m, unit_process_name = "swoi", unit_process_type = 'sw_onshore_intake')
        m = wt.design.add_unit_process(m = m, unit_process_name = "coag_floc", unit_process_type = 'coag_and_floc')
        m = wt.design.add_unit_process(m = m, unit_process_name = "tri_media_filtration", unit_process_type = 'tri_media_filtration')
        m = wt.design.add_unit_process(m = m, unit_process_name = "SAA", unit_process_type = 'sulfuric_acid_addition')
        m = wt.design.add_unit_process(m = m, unit_process_name = "SBA", unit_process_type = 'sodium_bisulfite_addition')
        m = wt.design.add_unit_process(m = m, unit_process_name = "cf", unit_process_type = 'cartridge_filtration')
        m = wt.design.add_unit_process(m = m, unit_process_name = "ro", unit_process_type = 'ro_deep')
        m = wt.design.add_unit_process(m = m, unit_process_name = "lime", unit_process_type = 'lime_softening')
        m = wt.design.add_unit_process(m = m, unit_process_name = "co2", unit_process_type = 'co2_addition')
        m = wt.design.add_unit_process(m = m, unit_process_name = "chlor", unit_process_type = 'chlorination_twb')
        m = wt.design.add_unit_process(m = m, unit_process_name = "ammonia", unit_process_type = 'ammonia_addition')
        m = wt.design.add_unit_process(m = m, unit_process_name = "TWS_24_hr", unit_process_type = 'treated_storage_24_hr')
        m = wt.design.add_unit_process(m = m, unit_process_name = "muni", unit_process_type = 'municipal_drinking')
        m = wt.design.add_unit_process(m = m, unit_process_name = "backwash", unit_process_type = 'backwash_solids_handling')
        m = wt.design.add_unit_process(m = m, unit_process_name = "surface", unit_process_type = 'surface_discharge')
        m = wt.design.add_unit_process(m = m, unit_process_name = "landfill", unit_process_type = 'landfill')
        

        # mixer and splitter for recycled water
        m.fs.mixer1 = Mixer1(default={"property_package": m.fs.water, "inlet_list": ["inlet1", "inlet2"]})

        ### SWAP THE SPLITTER FOR WASTE DISPOSAL WITH RECOVERY 0.95
        m.fs.splitter1 = Separator1(default={
            "property_package": m.fs.water,
            "ideal_separation": False,
            "outlet_list": ['outlet1', 'outlet2']})

        m.fs.splitter1.split_fraction[0, "outlet1"].fix(0.95)


        # connect unit models
        ### NOTE THE ARC METHOD IS PROBABLY EASIER FOR NOW ### (compared to  wt.design.connect_blocks)
        m.fs.arc1 = Arc(source=m.fs.source1.outlet, destination=m.fs.swoi.inlet)
        m.fs.arc2 = Arc(source=m.fs.swoi.outlet, destination=m.fs.coag_floc.inlet)
        m.fs.arc3 = Arc(source=m.fs.coag_floc.outlet, destination=m.fs.mixer1.inlet1) # for recycle
        m.fs.arc4 = Arc(source=m.fs.mixer1.outlet, destination=m.fs.tri_media_filtration.inlet) # for recycle
        m.fs.arc5 = Arc(source=m.fs.tri_media_filtration.waste, destination=m.fs.splitter1.inlet) # for recycle
        m.fs.arc6 = Arc(source=m.fs.splitter1.outlet1, destination=m.fs.mixer1.inlet2) # for recycle
        m.fs.arc7 = Arc(source=m.fs.tri_media_filtration.outlet, destination=m.fs.SAA.inlet)
        m.fs.arc8 = Arc(source=m.fs.SAA.outlet, destination=m.fs.SBA.inlet)
        m.fs.arc9 = Arc(source=m.fs.SBA.outlet, destination=m.fs.cf.inlet)
        m.fs.arc10 = Arc(source=m.fs.cf.outlet, destination=m.fs.ro.inlet)
        m.fs.arc11 = Arc(source=m.fs.ro.outlet, destination=m.fs.lime.inlet)
        m.fs.arc12 = Arc(source=m.fs.lime.outlet, destination=m.fs.co2.inlet)
        m.fs.arc13 = Arc(source=m.fs.co2.outlet, destination=m.fs.chlor.inlet)
        m.fs.arc14 = Arc(source=m.fs.chlor.outlet, destination=m.fs.ammonia.inlet)
        m.fs.arc15 = Arc(source=m.fs.ammonia.outlet, destination=m.fs.TWS_24_hr.inlet)
        m.fs.arc16 = Arc(source=m.fs.TWS_24_hr.outlet, destination=m.fs.muni.inlet)

    return m


